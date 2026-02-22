import logging
import os

import boto3


logger = logging.getLogger(__name__)


class NotificationGateway:
    def __init__(self, topic_arn: str | None = None, region: str | None = None):
        self.topic_arn = topic_arn or os.getenv("PROCESSING_NOTIFICATIONS_TOPIC_ARN")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self.topic_arn)

    def _client_or_none(self):
        if not self.enabled:
            return None
        if self._client is None:
            self._client = boto3.client("sns", region_name=self.region)
        return self._client

    def notify_processing_error(self, video_id: int, error_message: str, user_id: int | None = None) -> bool:
        client = self._client_or_none()
        if client is None:
            logger.info("Notificação de erro desativada (PROCESSING_NOTIFICATIONS_TOPIC_ARN não configurado)")
            return False

        user_part = f"Usuário: {user_id}\n" if user_id is not None else ""
        message = (
            "Falha no processamento de vídeo\n\n"
            f"Video ID: {video_id}\n"
            f"{user_part}"
            f"Erro: {error_message}"
        )

        client.publish(
            TopicArn=self.topic_arn,
            Subject="Falha no processamento de vídeo",
            Message=message,
        )
        return True
