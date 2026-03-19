"""
SEINENTAI4US - API FastAPI principale
Plateforme RAG pour le groupe des jeunes
dolnickenzanza@gmail.com
"""

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.routers import auth, documents, search, chat, admin
from seinentai4us_api.api.middleware.logging_middleware import RequestLoggingMiddleware

# ─── Logging structuré ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("seinentai4us")


# ─── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SEINENTAI4US API — démarrage...")
    logger.info(f"   Environnement : {settings.ENVIRONMENT}")
    logger.info(f"   Qdrant        : {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info(f"   MinIO         : {settings.MINIO_ENDPOINT}")
    logger.info(f"   Ollama        : {settings.OLLAMA_BASE_URL}")

    kafka_service = None
    kafka_thread = None

    # Évite un double démarrage en mode `uvicorn --reload` :
    # - le child définit RUN_MAIN=true en général
    # - le parent relance le code sans avoir besoin de consumer Kafka
    enable_kafka_consumer_default = "true" if settings.ENVIRONMENT == "development" else "false"
    enable_kafka_consumer = os.getenv("ENABLE_KAFKA_CONSUMER", enable_kafka_consumer_default).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    run_main = os.getenv("RUN_MAIN") is None or os.getenv("RUN_MAIN") == "true"

    # Initialisation des singletons RAG (MinIO/Qdrant/embeddings/chunking) au démarrage.
    # En mode test, on évite les chargements lourds.
    import sys
    is_pytest = "pytest" in sys.modules

    if run_main and not is_pytest:
        from seinentai4us_api.api.services.app_services import build_app_services
        from seinentai4us_api.api.services.rag_service import initialize_pipelines

        app.state.services = build_app_services()
        initialize_pipelines(
            retriever_pipeline=app.state.services.retriever_pipeline,
            generation_pipeline=app.state.services.generation_pipeline,
        )

        # Réutiliser les pipelines injectés côté consumer Kafka
        from services.kafka_consumer import configure_kafka_dependencies

        configure_kafka_dependencies(
            retriever_pipeline=app.state.services.retriever_pipeline,
            vector_store=app.state.services.vector_store,
        )

    if enable_kafka_consumer and run_main and not is_pytest:
        try:
            from services.kafka_consumer import KafkaService

            kafka_service = KafkaService()

            def _run_consumer():
                try:
                    if kafka_service.create_topics():
                        kafka_service.consume_messages()
                    else:
                        logger.error("Kafka topic creation impossible, consumer non démarré.")
                except Exception as e:
                    logger.exception(f"Consumer Kafka arrêté suite à une erreur: {e}")

            kafka_thread = threading.Thread(
                target=_run_consumer, name="kafka-consumer", daemon=True
            )
            kafka_thread.start()
            logger.info("Consumer Kafka démarré en arrière-plan.")
        except Exception as e:
            logger.exception(f"Impossible de démarrer le consumer Kafka: {e}")

    yield

    # Arrêt au shutdown
    if kafka_service is not None:
        try:
            logger.info("Arrêt du consumer Kafka...")
            kafka_service.stop()
        except Exception as e:
            logger.exception(f"Erreur pendant l'arrêt du consumer Kafka: {e}")
    if kafka_thread is not None:
        try:
            kafka_thread.join(timeout=10)
        except Exception:
            pass

    logger.info("🛑 SEINENTAI4US API — arrêt propre.")


# ─── Application ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="SEINENTAI4US API",
    description="""
## 🎌 Plateforme RAG pour le groupe des jeunes — SEINENTAI4US

API complète pour la gestion, l'indexation et l'interrogation de documents via un système RAG
(Retrieval-Augmented Generation) alimenté par Ollama, Qdrant et MinIO.

### Fonctionnalités
- 🔐 Authentification par token API
- 📄 Gestion de documents (upload, suppression, réindexation)
- 🔍 Recherche sémantique et hybride (BM25 + dense)
- 💬 Chat avec streaming SSE et historique de conversation
- 🏥 Monitoring système
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── State ────────────────────────────────────────────────────────────────────
app.state.limiter = limiter

# ─── Middlewares ──────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Gestionnaire rate limit ──────────────────────────────────────────────────
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─── Gestionnaire d'erreurs global ───────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée sur {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Une erreur interne s'est produite.",
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
        },
    )


# ─── Routeurs ─────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["🔐 Authentification"])
app.include_router(documents.router, prefix="/documents", tags=["📄 Documents"])
app.include_router(search.router,    prefix="/search",    tags=["🔍 Recherche"])
app.include_router(chat.router,      prefix="/chat",      tags=["💬 Chat"])
app.include_router(admin.router,     prefix="",           tags=["🏥 Système"])


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "SEINENTAI4US API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
