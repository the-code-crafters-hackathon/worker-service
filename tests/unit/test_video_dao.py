from unittest.mock import Mock

import pytest

from app.dao.video_dao import VideoDAO


class DummyVideo:
    def __init__(self, video_id=1, status=0, file_path="old"):
        self.id = video_id
        self.status = status
        self.file_path = file_path


def test_video_dao_update_video_status_success():
    db = Mock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = DummyVideo(video_id=1)

    dao = VideoDAO(db)
    updated = dao.update_video_status(video_id=1, status=1, file_path="outputs/new.zip")

    assert updated.status == 1
    assert updated.file_path == "outputs/new.zip"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(updated)


def test_video_dao_update_video_status_not_found():
    db = Mock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = None

    dao = VideoDAO(db)

    with pytest.raises(Exception) as exc_info:
        dao.update_video_status(video_id=99, status=1)

    assert "não encontrado" in str(exc_info.value)
