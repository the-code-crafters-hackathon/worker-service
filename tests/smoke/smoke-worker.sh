#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/.docker/docker-compose.yml"
SMOKE_ENV_FILE="$ROOT_DIR/.docker/.env.smoke"
LOCALSTACK_CONTAINER="localstack-worker-smoke"
NETWORK_NAME="video-upload-network"
QUEUE_URL="http://${LOCALSTACK_CONTAINER}:4566/000000000000/video-processing-queue"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

cleanup() {
  set +e
  cd "$ROOT_DIR" || exit 0
  WORKER_ENV_FILE=.env.smoke docker compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
  docker rm -f "$LOCALSTACK_CONTAINER" >/dev/null 2>&1 || true
  rm -f "$SMOKE_ENV_FILE"
}
trap cleanup EXIT

cd "$ROOT_DIR"

docker network inspect "$NETWORK_NAME" >/dev/null 2>&1 || docker network create "$NETWORK_NAME" >/dev/null

docker rm -f "$LOCALSTACK_CONTAINER" >/dev/null 2>&1 || true
docker run -d \
  --name "$LOCALSTACK_CONTAINER" \
  --network "$NETWORK_NAME" \
  -e SERVICES=sqs \
  -e DEFAULT_REGION=us-east-1 \
  localstack/localstack:latest >/dev/null

cat > "$SMOKE_ENV_FILE" <<EOF
APP_ENV=development
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://${LOCALSTACK_CONTAINER}:4566
AWS_S3_BUCKET=video-processor-bucket
DATABASE_URL=sqlite:////app/worker.db
DB_SECRET_NAME=
SQS_VIDEO_PROCESSING_QUEUE=${QUEUE_URL}
EOF

WORKER_ENV_FILE=.env.smoke docker compose -f "$COMPOSE_FILE" up -d --build >/dev/null

docker run --rm --network "$NETWORK_NAME" \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli \
  --endpoint-url="http://${LOCALSTACK_CONTAINER}:4566" \
  sqs create-queue --queue-name video-processing-queue >/dev/null

docker exec -i video_processor_worker python - <<'PY'
from pathlib import Path
from app.infrastructure.db.database import Base, engine, SessionLocal
from app.models.video import Video

Base.metadata.create_all(bind=engine)
Path('/app/uploads').mkdir(parents=True, exist_ok=True)

db = SessionLocal()
video = db.query(Video).filter(Video.id == 1).first()

if not video:
    db.add(Video(id=1, user_id=1, title='smoke-video', file_path='/app/uploads/smoke.mp4', status=0))
    db.commit()
else:
    video.status = 0
    video.file_path = '/app/uploads/smoke.mp4'
    db.commit()

db.close()
PY

docker exec video_processor_worker ffmpeg -f lavfi -i testsrc=size=640x360:rate=30 -t 2 -pix_fmt yuv420p -y /app/uploads/smoke.mp4 >/dev/null 2>&1

docker run --rm --network "$NETWORK_NAME" \
  -e AWS_ACCESS_KEY_ID=test \
  -e AWS_SECRET_ACCESS_KEY=test \
  -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli \
  --endpoint-url="http://${LOCALSTACK_CONTAINER}:4566" \
  sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body "{\"video_id\":1,\"video_path\":\"/app/uploads/smoke.mp4\",\"timestamp\":\"${TIMESTAMP}\"}" >/dev/null

STATUS="0"
for _ in $(seq 1 30); do
  STATUS=$(docker exec video_processor_worker python -c "from app.infrastructure.db.database import SessionLocal; from app.models.video import Video; db=SessionLocal(); v=db.query(Video).filter(Video.id==1).first(); print(v.status if v else -1); db.close()")
  if [[ "$STATUS" == "1" ]]; then
    break
  fi
  sleep 2
done

if [[ "$STATUS" != "1" ]]; then
  echo "[FAIL] Worker não atualizou status para 1"
  docker compose -f "$COMPOSE_FILE" logs --tail=200 video_processor_worker || true
  exit 1
fi

OUTPUT_PATH="/app/outputs/frames_${TIMESTAMP}.zip"
if ! docker exec video_processor_worker test -f "$OUTPUT_PATH"; then
  echo "[FAIL] Arquivo de saída não encontrado em ${OUTPUT_PATH}"
  docker compose -f "$COMPOSE_FILE" logs --tail=200 video_processor_worker || true
  exit 1
fi

echo "[OK] Smoke específico do worker concluído com sucesso"
