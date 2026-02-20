from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import tempfile

from app.gateways.video_processing_gateway import VideoProcessingGateway


def _fake_ffmpeg_success(cmd, capture_output=True, text=True):
    frame_pattern = cmd[-1]
    frame_1 = Path(frame_pattern.replace("%04d", "0001"))
    frame_2 = Path(frame_pattern.replace("%04d", "0002"))
    frame_1.parent.mkdir(parents=True, exist_ok=True)
    frame_1.write_bytes(b"img")
    frame_2.write_bytes(b"img")
    return SimpleNamespace(returncode=0, stderr="", stdout="")


def test_video_processing_gateway_initializes_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        gateway = VideoProcessingGateway(base_dir=Path(tmpdir))

        assert gateway.uploads_dir.exists()
        assert gateway.outputs_dir.exists()
        assert gateway.temp_dir.exists()


def test_video_processing_gateway_process_video_local_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        gateway = VideoProcessingGateway(base_dir=base_dir)

        video_path = base_dir / "uploads" / "video.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"video")

        with patch("app.gateways.video_processing_gateway.subprocess.run", side_effect=_fake_ffmpeg_success):
            zip_path, frame_count, images = gateway.process_video(str(video_path), "20260218_111500")

        assert Path(zip_path).exists()
        assert frame_count == 2
        assert len(images) == 2


def test_video_processing_gateway_process_video_production_uploads_to_s3(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        gateway = VideoProcessingGateway(base_dir=base_dir)

        video_path = base_dir / "uploads" / "video.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"video")

        mock_s3_gateway = Mock()
        mock_s3_gateway.bucket_name = "bucket-test"
        mock_s3_gateway.upload_video.return_value = True

        monkeypatch.setenv("APP_ENV", "production")

        with patch("app.gateways.video_processing_gateway.subprocess.run", side_effect=_fake_ffmpeg_success):
            with patch("app.gateways.video_processing_gateway.S3Gateway", return_value=mock_s3_gateway):
                zip_path, frame_count, _ = gateway.process_video(str(video_path), "20260218_112000")

        assert zip_path == "s3://bucket-test/outputs/frames_20260218_112000.zip"
        assert frame_count == 2
        mock_s3_gateway.upload_video.assert_called_once()


def test_video_processing_gateway_raises_when_ffmpeg_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        gateway = VideoProcessingGateway(base_dir=base_dir)

        video_path = base_dir / "uploads" / "video.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"video")

        fail_result = SimpleNamespace(returncode=1, stderr="error", stdout="")

        with patch("app.gateways.video_processing_gateway.subprocess.run", return_value=fail_result):
            try:
                gateway.process_video(str(video_path), "20260218_113000")
                assert False, "Expected exception"
            except Exception as exc:
                assert "FFmpeg error" in str(exc)
