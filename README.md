# 🎞️ Worker Service (Video Processing)

Serviço responsável por consumir mensagens da fila e processar vídeos com FFmpeg, gerando ZIP de frames e atualizando status no banco.

## Fluxo

1. Consome mensagem da `SQS_VIDEO_PROCESSING_QUEUE`
2. Resolve origem do vídeo (local ou `s3://...`)
3. Extrai frames com FFmpeg (1 fps)
4. Gera ZIP em `outputs/`
5. Atualiza status no banco:
   - `1` processado
   - `2` erro

## Estrutura

- `worker.py`: loop principal do worker
- `app/use_cases/process_video_use_case.py`: regra de negócio de processamento
- `app/gateways/video_processing_gateway.py`: FFmpeg + ZIP
- `app/gateways/s3_gateway.py`: download/upload S3
- `app/infrastructure/queue/sqs_consumer.py`: consumo de mensagens da fila
- `app/dao/video_dao.py`: persistência do status

## Executar local

```bash
make install
make test
make smoke
make run
```

## Executar com Docker

```bash
cp .docker/.env-example .docker/.env
docker compose -f .docker/docker-compose.yml build
docker compose -f .docker/docker-compose.yml up -d
```

## Variáveis de ambiente principais

- `APP_ENV` (`development` ou `production`)
- `DATABASE_URL` ou `DB_SECRET_NAME`
- `SQS_VIDEO_PROCESSING_QUEUE`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ENDPOINT_URL` (LocalStack/dev)
- `AWS_S3_BUCKET`

## Qualidade

- Testes unitários com `pytest`
- Smoke específico do worker em `tests/smoke/smoke-worker.sh`
- Cobertura com `pytest-cov`
- Configuração de análise no `sonar-project.properties`
- CI executa testes unitários + smoke do worker em pull requests
- CD valida quality gate do worker (unit + smoke) antes de build da imagem
- Smoke E2E completo (Upload -> Worker) permanece centralizado no repositório `infra`
