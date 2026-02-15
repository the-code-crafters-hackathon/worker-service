import logging
import os
from pathlib import Path
import boto3

logger = logging.getLogger(__name__)


class S3Gateway:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.bucket_name = os.getenv("AWS_S3_BUCKET", "video-processor-bucket")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.env = os.getenv("APP_ENV", "development")
        
        if self.env != "development":
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("AWS_ENDPOINT_URL")
            )
        
        logger.info(f"S3Gateway inicializado - Bucket: {self.bucket_name}, Env: {self.env}")

    def download_video(self, s3_key: str, local_path: str) -> bool:
        if self.env == "development":
            path = Path(local_path)
            if path.exists():
                logger.info(f"Arquivo local encontrado: {local_path}")
                return True
            else:
                logger.error(f"Arquivo não encontrado: {local_path}")
                return False
        
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Vídeo baixado do S3: {s3_key} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao baixar vídeo do S3: {str(e)}")
            return False

    def upload_video(self, local_path: str, s3_key: str) -> bool:
        if self.env == "development":
            logger.info(f"Modo desenvolvimento - arquivo mantido localmente: {local_path}")
            return True
        
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            logger.info(f"Vídeo enviado para S3: {local_path} -> {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar vídeo para S3: {str(e)}")
            return False
