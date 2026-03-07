FROM python:3.11-slim

WORKDIR /app

COPY kafka_service.py .
COPY minio_service.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python", "kafka_service.py"]