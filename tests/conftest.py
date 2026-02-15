import os
import pytest
from pathlib import Path

# Add project root to path
pytest_plugins = []

@pytest.fixture
def app_env(monkeypatch):
    """Set development environment variables"""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SQS_VIDEO_PROCESSING_QUEUE", "http://localhost:4566/000000000000/video-processing-queue")
