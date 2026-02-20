import os
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import worker


def test_extract_s3_key_from_uri():
    key = worker.VideoWorker._extract_s3_key("s3://my-bucket/uploads/video.mp4")
    assert key == "uploads/video.mp4"


def test_extract_s3_key_from_explicit_field():
    key = worker.VideoWorker._extract_s3_key("/local/path/video.mp4", explicit_s3_key="uploads/video.mp4")
    assert key == "uploads/video.mp4"


@patch("worker.SessionLocal")
@patch("worker.VideoDAO")
@patch("worker.ProcessVideoUseCase")
def test_process_message_success(mock_use_case_cls, mock_video_dao_cls, mock_session_local):
    mock_session = Mock()
    mock_session_local.return_value = mock_session

    mock_use_case = Mock()
    mock_use_case_cls.return_value = mock_use_case

    worker_instance = worker.VideoWorker()
    worker_instance.s3_gateway = Mock()

    result = worker_instance.process_message(
        {
            "video_id": 1,
            "video_path": "uploads/video.mp4",
            "timestamp": "20260218_120000",
            "user_id": 10,
        }
    )

    assert result is True
    mock_use_case.execute.assert_called_once_with(
        video_id=1,
        video_path="uploads/video.mp4",
        timestamp="20260218_120000",
    )
    mock_session.close.assert_called_once()


@patch("worker.SessionLocal")
@patch("worker.VideoDAO")
@patch("worker.ProcessVideoUseCase")
def test_process_message_downloads_s3_file_before_processing(mock_use_case_cls, mock_video_dao_cls, mock_session_local):
    mock_session = Mock()
    mock_session_local.return_value = mock_session

    mock_use_case = Mock()
    mock_use_case_cls.return_value = mock_use_case

    worker_instance = worker.VideoWorker()
    worker_instance.s3_gateway = Mock()

    def _download_side_effect(_s3_key, local_path):
        Path(local_path).write_bytes(b"video")
        return True

    worker_instance.s3_gateway.download_video.side_effect = _download_side_effect

    result = worker_instance.process_message(
        {
            "video_id": 2,
            "video_path": "s3://video-bucket/uploads/video.mp4",
            "timestamp": "20260218_121500",
            "user_id": 10,
        }
    )

    assert result is True
    args = mock_use_case.execute.call_args.kwargs
    assert args["video_id"] == 2
    assert args["timestamp"] == "20260218_121500"
    assert args["video_path"].endswith("_video.mp4")
    worker_instance.s3_gateway.download_video.assert_called_once()


def test_process_message_invalid_payload_returns_false():
    worker_instance = worker.VideoWorker()
    result = worker_instance.process_message({"video_id": 1})

    assert result is False
