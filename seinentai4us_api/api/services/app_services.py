import logging
from dataclasses import dataclass
from typing import Optional

from qdrant_client import QdrantClient

from seinentai4us_api.api.config import settings
from services.minio_service import MinIOService
from Ingestion.document_processor import DocumentProcessor
from Ingestion.embeddings import EmbeddingGenerator
from Ingestion.ingestion_pipeline import IngestionPipeline
from Ingestion.text_chunker import TextChunker
from Retrieval.retrieval_pipeline import RetrieverPipeline
from Retrieval.vector_store import VectorStore
from Generation.generation import GenerationPipeline

logger = logging.getLogger(__name__)


@dataclass
class AppServices:
    minio_service: MinIOService
    qdrant_client: QdrantClient
    embedding_generator: EmbeddingGenerator
    document_chunker: TextChunker
    vector_store: VectorStore
    ingestion_pipeline: IngestionPipeline
    retriever_pipeline: RetrieverPipeline
    generation_pipeline: GenerationPipeline


def build_app_services() -> AppServices:
    """
    Construit toutes les dépendances lourdes une seule fois.

    La création du modèle embedding et la connexion Qdrant/MinIO sont faites au démarrage via `lifespan`.
    """

    logger.info("Initialisation services lourds (lifespan)...")

    minio_service = MinIOService(secure=settings.MINIO_SECURE)
    qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    embedding_generator = EmbeddingGenerator(settings.EMBEDDING_MODEL)
    test_embedding = embedding_generator.generate_single("test")
    vector_size = len(test_embedding) if test_embedding is not None else 384
    logger.info(f"Dimension embeddings: {vector_size}")

    document_chunker = TextChunker(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    processor = DocumentProcessor()

    vector_store = VectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION,
        vector_size=vector_size,
        sparse_vector_name="keywords",
        sparse_model_name=settings.SPARSE_MODEL,
        client=qdrant_client,
    )

    ingestion_pipeline = IngestionPipeline(
        processor=processor,
        chunker=document_chunker,
        embedder=embedding_generator,
        minio_client=minio_service,
        vector_store=vector_store,
    )

    retriever_pipeline = RetrieverPipeline(
        embedder=embedding_generator,
        ingestion=ingestion_pipeline,
        vector_store=vector_store,
        minio_client=minio_service,
    )

    generation_pipeline = GenerationPipeline()

    return AppServices(
        minio_service=minio_service,
        qdrant_client=qdrant_client,
        embedding_generator=embedding_generator,
        document_chunker=document_chunker,
        vector_store=vector_store,
        ingestion_pipeline=ingestion_pipeline,
        retriever_pipeline=retriever_pipeline,
        generation_pipeline=generation_pipeline,
    )

