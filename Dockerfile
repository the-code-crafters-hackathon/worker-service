FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY .docker/bin/config/requirements.txt ./requirements.txt

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY worker.py ./worker.py

CMD ["python", "worker.py"]
