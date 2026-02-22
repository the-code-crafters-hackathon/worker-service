from unittest.mock import Mock

from app.gateways.notification_gateway import NotificationGateway


def test_notification_gateway_disabled_without_topic(monkeypatch):
    monkeypatch.delenv("PROCESSING_NOTIFICATIONS_TOPIC_ARN", raising=False)

    gateway = NotificationGateway(topic_arn=None)

    assert gateway.enabled is False
    assert gateway._client_or_none() is None
    assert gateway.notify_processing_error(video_id=1, error_message="erro") is False


def test_notification_gateway_publishes_message(monkeypatch):
    mock_client = Mock()
    boto3_factory = Mock(return_value=mock_client)

    monkeypatch.setattr("app.gateways.notification_gateway.boto3.client", boto3_factory)

    gateway = NotificationGateway(topic_arn="arn:aws:sns:us-east-1:123:topic", region="us-east-1")

    assert gateway.enabled is True
    assert gateway.notify_processing_error(video_id=10, error_message="ffmpeg error", user_id=99) is True

    boto3_factory.assert_called_once_with("sns", region_name="us-east-1")
    mock_client.publish.assert_called_once()

    kwargs = mock_client.publish.call_args.kwargs
    assert kwargs["TopicArn"] == "arn:aws:sns:us-east-1:123:topic"
    assert "Video ID: 10" in kwargs["Message"]
    assert "Usuário: 99" in kwargs["Message"]


def test_notification_gateway_reuses_client(monkeypatch):
    mock_client = Mock()
    boto3_factory = Mock(return_value=mock_client)

    monkeypatch.setattr("app.gateways.notification_gateway.boto3.client", boto3_factory)

    gateway = NotificationGateway(topic_arn="arn:aws:sns:us-east-1:123:topic")
    gateway.notify_processing_error(video_id=1, error_message="e1")
    gateway.notify_processing_error(video_id=2, error_message="e2")

    boto3_factory.assert_called_once()
    assert mock_client.publish.call_count == 2
