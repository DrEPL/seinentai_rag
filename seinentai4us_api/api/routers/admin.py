"""
Router Admin / Système — SEINENTAI4US
GET /health - Santé du système
"""

import logging
import time
from datetime import datetime

import requests

from fastapi import APIRouter

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.models.schemas import HealthResponse, ServiceHealth

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


def _check_qdrant() -> ServiceHealth:
    t0 = time.perf_counter()
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=3)
        client.get_collections()
        return ServiceHealth(
            name="qdrant",
            status="ok",
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except Exception as e:
        return ServiceHealth(name="qdrant", status="error", details=str(e))


def _check_minio() -> ServiceHealth:
    t0 = time.perf_counter()
    try:
        from services.minio_service import MinIOService
        minio = MinIOService()
        minio.client.list_buckets()
        return ServiceHealth(
            name="minio",
            status="ok",
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except Exception as e:
        return ServiceHealth(name="minio", status="error", details=str(e))


def _check_ollama() -> ServiceHealth:
    t0 = time.perf_counter()
    try:
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        return ServiceHealth(
            name="ollama",
            status="ok",
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
            details=f"Modèles disponibles : {', '.join(models) or 'aucun'}",
        )
    except Exception as e:
        return ServiceHealth(name="ollama", status="error", details=str(e))


def _check_kafka() -> ServiceHealth:
    t0 = time.perf_counter()
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=2000,
        )
        admin.close()
        return ServiceHealth(
            name="kafka",
            status="ok",
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except Exception as e:
        return ServiceHealth(name="kafka", status="degraded", details=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Santé du système SEINENTAI4US",
    tags=["🏥 Système"],
)
async def health():
    """
    Vérifie la disponibilité de tous les services :
    - **Qdrant** (base vectorielle)
    - **MinIO** (stockage objet)
    - **Ollama** (LLM)
    - **Kafka** (messaging — dégradé toléré)

    Le statut global est :
    - `healthy` si tous les services critiques (Qdrant, MinIO, Ollama) sont OK
    - `degraded` si Kafka est inaccessible mais le reste fonctionne
    - `unhealthy` si au moins un service critique est en erreur
    """
    checks = [
        _check_qdrant(),
        _check_minio(),
        _check_ollama(),
        _check_kafka(),
    ]

    critical = {s.name for s in checks if s.name != "kafka"}
    errors = {s.name for s in checks if s.status == "error"}
    kafka_degraded = any(s.name == "kafka" and s.status != "ok" for s in checks)

    if errors & critical:
        overall = "unhealthy"
    elif kafka_degraded or (errors - critical):
        overall = "degraded"
    else:
        overall = "healthy"

    return HealthResponse(
        status=overall,
        timestamp=datetime.utcnow(),
        services=checks,
        uptime_seconds=round(time.time() - _start_time, 1),
    )
