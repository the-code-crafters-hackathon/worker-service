import os
import pytest
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SQS_VIDEO_PROCESSING_QUEUE", "http://localhost:4566/000000000000/video-processing-queue")

# Add project root to path
pytest_plugins = []

@pytest.fixture(autouse=True)
def app_env(monkeypatch):
    """Set development environment variables"""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SQS_VIDEO_PROCESSING_QUEUE", "http://localhost:4566/000000000000/video-processing-queue")
