# Development Makefile for Video Processor Worker

.PHONY: help docker-up docker-down docker-logs install run test clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Run worker locally"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up files"

install:
	pip install -r .docker/bin/requirements.txt

run:
	python worker.py

docker-up:
	docker-compose -f .docker/docker-compose.yml up -d

docker-down:
	docker-compose -f .docker/docker-compose.yml down

docker-logs:
	docker-compose -f .docker/docker-compose.yml logs -f video_processor_worker

docker-build:
	docker-compose -f .docker/docker-compose.yml build

test:
	pytest tests/ -v --cov=app

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
