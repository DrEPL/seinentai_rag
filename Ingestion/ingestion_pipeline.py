import logging
import hashlib
from datetime import datetime
import os

# from .config import Config
# from Retrieval.vector_store import VectorStore
from Ingestion.document_processor import DocumentProcessor
from services.minio_service import MinIOService
from Ingestion.text_chunker import TextChunker
from Ingestion.embeddings import EmbeddingGenerator
from dotenv import load_dotenv

from utils.functions import generate_doc_id


load_dotenv('../.env')

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Pipeline RAG complet"""
    
    def __init__(self):
        # self.config = Config()
        
        # Initialiser les composants
        self.processor = DocumentProcessor()
        self.chunker = TextChunker(
            chunk_size=os.getenv('CHUNK_SIZE', 500),
            chunk_overlap=os.getenv('CHUNK_OVERLAP', 20)
        )
        self.embedder = EmbeddingGenerator(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
        
        # MinIO client
        self.minio_client = MinIOService()
    
    def process_document(self, bucket: str, filename: str) -> tuple[list, list]:
        """
        Traite un document depuis MinIO
        
        Args:
            bucket: Nom du bucket MinIO
            filename: Nom du fichier
            
        Retourne:
            - embeddings: Liste de vecteurs (liste de float) ou []
            - chunks: Liste de dictionnaires de métadonnées ou []
        """
        logger.info(f"🔄 Traitement du document: {bucket}/{filename}")
        
        try:
            # 1. Télécharger depuis MinIO
            content = self.minio_client.get_object(bucket, filename)
            
            # 2. Générer un hash du contenu
            content_hash = hashlib.md5(content).hexdigest()
            doc_id = generate_doc_id(filename, content_hash)
            
            # 3. Parser le document
            text = self.processor.process(content, filename)
            if not text:
                logger.warning(f"⚠️ Document vide ou non traitable: {filename}")
                return [], []
            
            # 4. Découper en chunks
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
                return [], []
            
            # 5. Générer les embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.generate(texts)
            
            if not embeddings :
                logger.error(f"❌ Erreur génération embeddings: liste vide")
                return [], []
            
            if len(embeddings) != len(chunks):
                logger.error(f"❌ Incohérence embeddings ({len(embeddings)}) / chunks ({len(chunks)})")
                return [], []
            
            logger.info(f"✅ Document traité avec succès: {filename} ({len(chunks)} chunks)")
            
            return embeddings, chunks
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filename}: {e}")
            import traceback
            traceback.print_exc()
            return [], []


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