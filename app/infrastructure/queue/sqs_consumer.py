import json
import logging
import os
import time
from typing import Optional, Dict, Any
import boto3

logger = logging.getLogger(__name__)

class SQSConsumer:
    def __init__(self):
        self.queue_url = os.getenv("SQS_VIDEO_PROCESSING_QUEUE")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        self.client = boto3.client(
            'sqs',
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=os.getenv("AWS_ENDPOINT_URL")  # For LocalStack in development
        )
        
        logger.info(f"SQS Consumer inicializado - Queue: {self.queue_url}")

    def receive_message(self, wait_time: int = 20, max_messages: int = 1) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time
            )
            
            if 'Messages' in response:
                return response['Messages'][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao receber mensagem do SQS: {str(e)}")
            return None

    def delete_message(self, receipt_handle: str) -> bool:
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info("Mensagem deletada do SQS com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar mensagem do SQS: {str(e)}")
            return False

    def parse_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            body = json.loads(message['Body'])
            return body
        except Exception as e:
            logger.error(f"Erro ao fazer parse da mensagem SQS: {str(e)}")
            return None
