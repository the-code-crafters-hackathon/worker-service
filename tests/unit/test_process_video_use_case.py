from unittest.mock import Mock

from app.use_cases.process_video_use_case import ProcessVideoUseCase


def test_process_video_use_case_success_updates_status_processed():
    processing_gateway = Mock()
    video_dao = Mock()
    s3_gateway = Mock()

    processing_gateway.process_video.return_value = ("outputs/frames_20260218.zip", 10, ["frame_0001.png"])

    use_case = ProcessVideoUseCase(
        processing_gateway=processing_gateway,
        video_dao=video_dao,
        s3_gateway=s3_gateway,
    )

    use_case.execute(video_id=1, video_path="uploads/video.mp4", timestamp="20260218_101010")

    processing_gateway.process_video.assert_called_once_with("uploads/video.mp4", "20260218_101010")
    video_dao.update_video_status.assert_called_once_with(
        video_id=1,
        status=1,
        file_path="outputs/frames_20260218.zip",
    )


def test_process_video_use_case_error_updates_status_error():
    processing_gateway = Mock()
    video_dao = Mock()

    processing_gateway.process_video.side_effect = Exception("ffmpeg error")

    use_case = ProcessVideoUseCase(
        processing_gateway=processing_gateway,
        video_dao=video_dao,
    )

    use_case.execute(video_id=1, video_path="uploads/video.mp4", timestamp="20260218_101010")

    video_dao.update_video_status.assert_called_once_with(video_id=1, status=2)


def test_process_video_use_case_error_sends_notification_when_gateway_provided():
    processing_gateway = Mock()
    video_dao = Mock()
    notification_gateway = Mock()

    processing_gateway.process_video.side_effect = Exception("ffmpeg error")
    video_dao.get_video_by_id.return_value = Mock(user_id=99)

    use_case = ProcessVideoUseCase(
        processing_gateway=processing_gateway,
        video_dao=video_dao,
        notification_gateway=notification_gateway,
    )

    use_case.execute(video_id=10, video_path="uploads/video.mp4", timestamp="20260218_101010")

    notification_gateway.notify_processing_error.assert_called_once_with(
        video_id=10,
        error_message="ffmpeg error",
        user_id=99,
    )
