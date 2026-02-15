import logging
import os
from pathlib import Path
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
        self.processing_gateway = VideoProcessingGateway(base_dir=self.base_dir)
        self.s3_gateway = S3Gateway(base_dir=self.base_dir)
        
    def process_message(self, message_body: dict) -> bool:
        try:
            video_id = message_body.get("video_id")
            video_path = message_body.get("video_path")
            timestamp = message_body.get("timestamp")
            
            if not all([video_id, video_path, timestamp]):
                logger.error(f"Mensagem inválida: faltam campos obrigatórios. Mensagem: {message_body}")
                return False
            
            db = SessionLocal()
            
            try:
                video_dao = VideoDAO(db)
                use_case = ProcessVideoUseCase(
                    processing_gateway=self.processing_gateway,
                    video_dao=video_dao,
                    s3_gateway=self.s3_gateway
                )
                
                use_case.execute(
                    video_id=video_id,
                    video_path=video_path,
                    timestamp=timestamp
                )
                logger.info(f"Vídeo {video_id} processado com sucesso")

                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
            return False

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
