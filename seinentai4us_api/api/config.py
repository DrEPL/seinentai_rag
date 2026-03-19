"""
Configuration centralisée — SEINENTAI4US
Toutes les variables d'environnement sont lues ici.
"""

import os
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "seinentai4us-super-secret-key-changez-moi-en-prod"
    TOKEN_EXPIRE_HOURS: int = 24
    CORS_ORIGINS: List[str] = ["*"]

    # ── MinIO ─────────────────────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "pdf-bucket"
    MINIO_SECURE: bool = False

    # ── Qdrant ────────────────────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPARSE_MODEL: str = "Qdrant/bm25"

    # ── Ollama / LLM ──────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "mistral-large-3:675b-cloud"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2048
    DEFAULT_TEMPLATE: str = "default"

    # ── Chunking ──────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 80

    # ── Kafka ─────────────────────────────────────────────────────────────────
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "minio-events"

    # ── Recherche ─────────────────────────────────────────────────────────────
    DEFAULT_SEARCH_LIMIT: int = 5
    DEFAULT_SCORE_THRESHOLD: float = 0.0

    # ── Documents (extensions supportées) ───────────────────────────────────
    SUPPORTED_DOCUMENT_EXTENSIONS: List[str] = [
        ".pdf",
        ".docx",
        ".md",
        ".markdown",
        ".txt",
        ".csv",
        ".json",
    ]

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
