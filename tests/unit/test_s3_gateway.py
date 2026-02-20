from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from app.gateways.s3_gateway import S3Gateway


def test_s3_gateway_download_video_in_development_with_local_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APP_ENV", "development")

        local_file = Path(tmpdir) / "video.mp4"
        local_file.write_bytes(b"video")

        gateway = S3Gateway(base_dir=Path(tmpdir))

        assert gateway.download_video("uploads/video.mp4", str(local_file)) is True


def test_s3_gateway_download_video_in_development_missing_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APP_ENV", "development")

        local_file = Path(tmpdir) / "missing.mp4"
        gateway = S3Gateway(base_dir=Path(tmpdir))

        assert gateway.download_video("uploads/missing.mp4", str(local_file)) is False


def test_s3_gateway_upload_video_in_development(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APP_ENV", "development")

        local_file = Path(tmpdir) / "video.mp4"
        local_file.write_bytes(b"video")

        gateway = S3Gateway(base_dir=Path(tmpdir))

        assert gateway.upload_video(str(local_file), "outputs/video.zip") is True


def test_s3_gateway_upload_video_in_production(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("AWS_REGION", "us-east-1")

        mock_client = Mock()
        with patch("app.gateways.s3_gateway.boto3.client", return_value=mock_client):
            gateway = S3Gateway(base_dir=Path(tmpdir))
            result = gateway.upload_video("/tmp/video.zip", "outputs/video.zip")

        assert result is True
        mock_client.upload_file.assert_called_once_with("/tmp/video.zip", gateway.bucket_name, "outputs/video.zip")
