import json
import logging
import hashlib
from datetime import datetime
import os
from pathlib import Path
from typing import Optional
from Ingestion.document_processor import DocumentProcessor
from services.minio_service import MinIOService
from Ingestion.text_chunker import TextChunker
from Ingestion.embeddings import EmbeddingGenerator
from dotenv import load_dotenv

from utils.functions import generate_doc_id


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Pipeline RAG complet"""
    
    def __init__(
        self,
        processor: Optional[DocumentProcessor] = None,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[EmbeddingGenerator] = None,
        minio_client: Optional[MinIOService] = None,
        vector_store=None,
    ):
        # Note: `vector_store` est optionnel mais recommandé pour éviter toute recréation côté Qdrant.
        self.processor = processor or DocumentProcessor()
        self.chunker = chunker or TextChunker(
            chunk_size=int(os.getenv('CHUNK_SIZE', 500)),
            chunk_overlap=int(os.getenv('CHUNK_OVERLAP', 50)),
        )
        self.embedder = embedder or EmbeddingGenerator(
            os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        )

        self.minio_client = minio_client or MinIOService()
        self.vector_store = vector_store
        if self.vector_store is None:
            # Fallback (non utilisé en production avec lifespan, mais utile pour scripts/tests).
            from Retrieval.vector_store import VectorStore

            self.vector_store = VectorStore()
    
    def process_document(self, bucket: str, filename: str) -> tuple[list, list, Optional[str]]:
        """
        Traite un document depuis MinIO
        
        Args:
            bucket: Nom du bucket MinIO
            filename: Nom du fichier
            
        Retourne:
            - embeddings: Liste de vecteurs (liste de float) ou []
            - chunks: Liste de dictionnaires de métadonnées ou []
            - doc_id: string ou None
        """
        logger.info(f"🔄 Traitement du document: {bucket}/{filename}")
        
        try:
            # 1. Télécharger depuis MinIO
            content = self.minio_client.get_object(bucket, filename)
            
            # 2. Générer un hash du contenu
            content_hash = hashlib.md5(content).hexdigest()
            doc_id = generate_doc_id(filename, content_hash)
            
            # 3. VÉRIFIER SI LE DOCUMENT EXISTE DÉJÀ
            if self._document_exists(doc_id):
                logger.info(f"⏭️ Document déjà indexé: {filename} (hash: {content_hash[:8]}...)")
                return [], [], None
            
            # 4. Parser le document
            text = self.processor.process(content, filename)
            if not text:
                logger.warning(f"⚠️ Document vide ou non traitable: {filename}")
                return [], [], None
            
            # 5. Découper en chunks
            chunks = self.chunker.chunk_with_metadata(
                text,
                doc_id=doc_id,
                filename=filename,
                metadata={
                    'bucket': bucket,
                    'content_hash': content_hash,
                    'processed_at': datetime.now().isoformat()
                }
            )
            
            if not chunks:
                logger.warning(f"⚠️ Aucun chunk généré: {filename}")
                return [], [], None
            
            # 6. Générer les embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.generate(texts)
            
            if not embeddings :
                logger.error(f"❌ Erreur génération embeddings: liste vide")
                return [], [], None
            
            if len(embeddings) != len(chunks):
                logger.error(f"❌ Incohérence embeddings ({len(embeddings)}) / chunks ({len(chunks)})")
                return [], [], None
            
            logger.info(f"✅ Document traité avec succès: {filename} ({len(chunks)} chunks)")
            
            return embeddings, chunks, doc_id
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filename}: {e}")
            import traceback
            traceback.print_exc()
            return [], [], None
        

    def _document_exists(self, doc_id: str) -> bool:
        """Vérifie si un document existe déjà dans Qdrant"""
        try:
            # Chercher un point avec ce doc_id dans les métadonnées
            from qdrant_client.http import models
            results = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_id",
                            match=models.MatchValue(value=doc_id)
                        )
                    ]
                ),
                limit=1
            )
            return len(results[0]) > 0
        except Exception as e:
            logger.error(f"Erreur vérification existence: {e}")
            return False

    def _record_document(self, doc_id: str, filename: str, content_hash: str, num_chunks: int):
        """Enregistre le document dans un registre (optionnel)"""
        # Option 1: Stocker dans un fichier JSON local
        registry_file = "document_registry.json"
        registry = {}
        
        if os.path.exists(registry_file):
            with open(registry_file, 'r') as f:
                registry = json.load(f)
        
        registry[doc_id] = {
            "filename": filename,
            "content_hash": content_hash,
            "num_chunks": num_chunks,
            "indexed_at": datetime.now().isoformat()
        }
        
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)


# Fonction utilitaire pour le callback Kafka
def rag_callback(bucket: str, filename: str, event: dict):
    """Callback pour Kafka"""
    logger.info(f"🚀 Déclenchement du pipeline RAG pour {bucket}/{filename}")
    pipeline = IngestionPipeline()
    success = pipeline.process_document(bucket, filename)
    
    if success:
        logger.info(f"✅ Pipeline RAG terminé pour {filename}")
    else:
        logger.error(f"❌ Pipeline RAG échoué pour {filename}")