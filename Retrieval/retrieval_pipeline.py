import logging
import hashlib
import json
from typing import Optional
from datetime import datetime
from minio import Minio
import os

from hybrid_retriever import HybridRetriever
from vector_store import VectorStore
from Ingestion.document_processor import DocumentProcessor
from Ingestion.text_chunker import TextChunker
from Ingestion.embeddings import EmbeddingGenerator
from dotenv import load_dotenv


load_dotenv('./.env')

logger = logging.getLogger(__name__)

class RetrieverPipeline:
    """Pipeline Retriever"""
    
    def __init__(self):
        # self.config = Config()
        
        # Initialiser les composants
        self.processor = DocumentProcessor()
        self.chunker = TextChunker(
            chunk_size=os.getenv('CHUNK_SIZE', 500),
            chunk_overlap=os.getenv('CHUNK_OVERLAP', 20)
        )
        self.embedder = EmbeddingGenerator(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
        # Obtenir la dimension du modèle (test avec un texte exemple)
        test_embedding = self.embedder.generate_single("test")
        if test_embedding is not None:
            self.vector_size = len(test_embedding)
            
        # Initialisation du store
        self.vector_store = VectorStore(host="localhost",
                            port=6333,
                            sparse_model_name="Qdrant/bm25",  # ou "prithivida/Splade_PP_en_v1"
                            collection_name="test_Robert",
                            vector_size=self.vector_size if self.vector_size else None
                        )
        
        # Initialisation de retrevier
        self.hybrid_retriever = HybridRetriever(self.vector_store)
        
        # MinIO client
        self.minio_client = Minio(
            os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key= os.environ.get("MINIO_ACCESS_KEY","minio"),
            secret_key= os.environ.get("MINIO_SECRET_KEY","minio123"), 
            secure=False
        )
        
        # Créer la collection si nécessaire
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialise le vector store"""
        self.vector_store.create_collection()
    
    def _generate_doc_id(self, filename: str, content_hash: str) -> str:
        """Génère un ID unique pour un document"""
        unique_str = f"{filename}_{content_hash}_{datetime.now().isoformat()}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def process_document(self, bucket: str, filename: str) -> bool:
        """
        Traite un document depuis MinIO
        
        Args:
            bucket: Nom du bucket MinIO
            filename: Nom du fichier
            
        Returns:
            True si succès
        """
        logger.info(f"🔄 Traitement du document: {bucket}/{filename}")
        
        try:
            # 1. Télécharger depuis MinIO
            response = self.minio_client.get_object(bucket, filename)
            content = response.read()
            response.close()
            response.release_conn()
            
            # 2. Générer un hash du contenu
            content_hash = hashlib.md5(content).hexdigest()
            doc_id = self._generate_doc_id(filename, content_hash)
            
            # 3. Parser le document
            text = self.processor.process(content, filename)
            if not text:
                logger.warning(f"⚠️ Document vide ou non traitable: {filename}")
                return False
            
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
                return False
            
            # 5. Générer les embeddings
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.generate(texts)
            
            if not embeddings or len(embeddings) != len(chunks):
                logger.error(f"❌ Erreur génération embeddings")
                return False
            
            # 6. Indexer dans Qdrant
            success = self.vector_store.index_documents(chunks, embeddings)
            
            if success:
                logger.info(f"✅ Document traité avec succès: {filename}")
                return True
            else:
                logger.error(f"❌ Échec indexation: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filename}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, limit: int = 5, score_threshold: float = 0.0, use_hybrid: float = True) -> list:
        """
        Recherche des documents similaires à une requête
        
        Args:
            query: Texte de la requête
            limit: Nombre de résultats
            score_threshold: Seuil de score minimal entre 0.0 et 1.0
            use_hybrid: True = recherche hybride, False = dense only
            
        Returns:
            Liste des documents pertinents
        """
        # Générer l'embedding de la requête
        query_embedding = self.embedder.generate_single(query)
        if query_embedding is None:
            return []
        
        # Rechercher
        results = self.hybrid_retriever.retrieve(query_text=query,query_embedding=query_embedding, limit=limit, score_threshold=score_threshold, use_hybrid=use_hybrid)
        
        logger.info(f"🔍 {len(results)} résultats pour: '{query[:50]}...'")
        return results


# Fonction utilitaire pour le callback Kafka
def rag_callback(bucket: str, filename: str, event: dict):
    """Callback pour Kafka"""
    logger.info(f"🚀 Déclenchement du pipeline RAG pour {bucket}/{filename}")
    pipeline = RetrieverPipeline()
    success = pipeline.process_document(bucket, filename)
    
    if success:
        logger.info(f"✅ Pipeline RAG terminé pour {filename}")
    else:
        logger.error(f"❌ Pipeline RAG échoué pour {filename}")