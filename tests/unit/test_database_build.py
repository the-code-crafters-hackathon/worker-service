import pytest

from app.infrastructure.db.database import _build_db_url


def test_build_db_url_prefers_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_worker.db")
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_SECRET_NAME", raising=False)

    assert _build_db_url() == "sqlite:///./test_worker.db"


def test_build_db_url_raises_when_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_SECRET_NAME", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        _build_db_url()

    assert "Database configuration error" in str(exc_info.value)
