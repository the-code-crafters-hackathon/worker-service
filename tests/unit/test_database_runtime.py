import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.infrastructure.db import database


def test_build_db_url_prefers_sqlalchemy_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./sqlalchemy_worker.db")
    monkeypatch.delenv("DB_SECRET_NAME", raising=False)

    assert database._build_db_url() == "sqlite:///./sqlalchemy_worker.db"


def test_build_db_url_from_secret_success(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_SECRET_NAME", "hackathon/db")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    secret_json = (
        '{"host":"db.local","port":5432,"username":"user","password":"p@ss","dbname":"videos"}'
    )

    mock_sm = Mock()
    mock_sm.get_secret_value.return_value = {"SecretString": secret_json}
    fake_boto3 = SimpleNamespace(client=Mock(return_value=mock_sm))

    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    url = database._build_db_url()

    assert url == "postgresql://user:p%40ss@db.local:5432/videos"


def test_build_db_url_from_secret_missing_fields_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_SECRET_NAME", "hackathon/db")

    secret_json = '{"host":"db.local","username":"user"}'

    mock_sm = Mock()
    mock_sm.get_secret_value.return_value = {"SecretString": secret_json}
    fake_boto3 = SimpleNamespace(client=Mock(return_value=mock_sm))

    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)

    with pytest.raises(RuntimeError) as exc_info:
        database._build_db_url()

    assert "could not build DB URL" in str(exc_info.value)


def test_get_db_closes_session(monkeypatch):
    mock_session = Mock()
    monkeypatch.setattr(database, "SessionLocal", Mock(return_value=mock_session))

    generator = database.get_db()
    yielded = next(generator)
    assert yielded is mock_session

    with pytest.raises(StopIteration):
        next(generator)

    mock_session.close.assert_called_once()
