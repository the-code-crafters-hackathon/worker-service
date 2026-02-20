import logging
from pathlib import Path
from typing import Optional
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.queue.sqs_consumer import SQSConsumer
from app.dao.video_dao import VideoDAO
from app.gateways.video_processing_gateway import VideoProcessingGateway
from app.gateways.s3_gateway import S3Gateway
from app.use_cases.process_video_use_case import ProcessVideoUseCase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoWorker:
    def __init__(self):
        self.sqs_consumer = SQSConsumer()
        self.base_dir = Path(__file__).resolve().parents[0]
        self.uploads_dir = self.base_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.processing_gateway = VideoProcessingGateway(base_dir=self.base_dir)
        self.s3_gateway = S3Gateway(base_dir=self.base_dir)

    @staticmethod
    def _extract_s3_key(video_path: str, explicit_s3_key: Optional[str] = None) -> Optional[str]:
        if explicit_s3_key:
            return explicit_s3_key.lstrip("/")

        if not video_path.startswith("s3://"):
            return None

        path_without_schema = video_path[5:]
        path_parts = path_without_schema.split("/", 1)
        if len(path_parts) < 2:
            return None

        return path_parts[1]

    def _ensure_local_video_path(self, video_path: str, timestamp: str, s3_key: Optional[str] = None) -> str:
        resolved_s3_key = self._extract_s3_key(video_path, s3_key)

        if not resolved_s3_key:
            return video_path

        local_filename = Path(resolved_s3_key).name or f"video_{timestamp}.mp4"
        local_path = self.uploads_dir / f"{timestamp}_{local_filename}"

        download_success = self.s3_gateway.download_video(resolved_s3_key, str(local_path))
        if not download_success:
            raise RuntimeError(f"Falha ao baixar vídeo do S3 para processamento: {resolved_s3_key}")

        return str(local_path)
        
    def process_message(self, message_body: dict) -> bool:
        success = False
        processing_video_path: Optional[str] = None
        db = None

        try:
            video_id = message_body.get("video_id")
            video_path = message_body.get("video_path")
            timestamp = message_body.get("timestamp")
            s3_key = message_body.get("s3_key")
            
            if not all([video_id, video_path, timestamp]):
                logger.error(f"Mensagem inválida: faltam campos obrigatórios. Mensagem: {message_body}")
                return False

            processing_video_path = self._ensure_local_video_path(
                video_path=video_path,
                timestamp=timestamp,
                s3_key=s3_key,
            )
            
            db = SessionLocal()

            video_dao = VideoDAO(db)
            use_case = ProcessVideoUseCase(
                processing_gateway=self.processing_gateway,
                video_dao=video_dao,
                s3_gateway=self.s3_gateway
            )

            use_case.execute(
                video_id=video_id,
                video_path=processing_video_path,
                timestamp=timestamp
            )
            logger.info(f"Vídeo {video_id} processado com sucesso")
            success = True
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)

        finally:
            if db is not None:
                db.close()

            if processing_video_path and processing_video_path != message_body.get("video_path"):
                local_file = Path(processing_video_path)
                if local_file.exists():
                    local_file.unlink()

        return success

    def run(self):
        logger.info("Iniciando Video Processor Worker")
        
        while True:
            try:
                message = self.sqs_consumer.receive_message(wait_time=20)
                
                if not message:
                    logger.debug("Nenhuma mensagem disponível na fila")
                    continue
                
                logger.info(f"Mensagem recebida: {message['MessageId']}")
                
                message_body = self.sqs_consumer.parse_message(message)
                
                if not message_body:
                    self.sqs_consumer.delete_message(message['ReceiptHandle'])
                    continue
                
                success = self.process_message(message_body)
                
                if success:
                    self.sqs_consumer.delete_message(message['ReceiptHandle'])
                else:
                    logger.warning(f"Erro ao processar mensagem {message['MessageId']}")
                    
            except KeyboardInterrupt:
                logger.info("Worker interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro no worker loop: {str(e)}", exc_info=True)
                import time
                time.sleep(5)


if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()
