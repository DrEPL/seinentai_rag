FROM python:3.11-slim

WORKDIR /app

COPY create_topics.py .

RUN pip install confluent-kafka

CMD ["python", "create_topics.py"]