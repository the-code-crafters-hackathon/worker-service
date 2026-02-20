from app.entities.video import ProcessingMessage, Video


def test_video_entity_defaults_and_fields():
    video = Video(user_id=10, title="t", file_path="uploads/v.mp4", status=0)

    assert video.id is None
    assert video.user_id == 10
    assert video.title == "t"
    assert video.file_path == "uploads/v.mp4"
    assert video.status == 0


def test_processing_message_entity_fields():
    message = ProcessingMessage(
        video_id=1,
        video_path="s3://bucket/uploads/v.mp4",
        timestamp="20260220_220000",
        user_id=99,
    )

    assert message.video_id == 1
    assert message.video_path.endswith("v.mp4")
    assert message.timestamp == "20260220_220000"
    assert message.user_id == 99
