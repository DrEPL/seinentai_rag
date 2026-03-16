import logging
import os
from Ingestion.ingestion_pipeline import IngestionPipeline
from Retrieval.hybrid_retriever import HybridRetriever
from services.minio_service import MinIOService
from Retrieval.vector_store import VectorStore
from Ingestion.embeddings import EmbeddingGenerator
from dotenv import load_dotenv


load_dotenv('../.env')

logger = logging.getLogger(__name__)

class RetrieverPipeline:
    """Pipeline Retriever"""
    
    def __init__(self):

        self.embedder = EmbeddingGenerator(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))
        # # Obtenir la dimension du modèle (test avec un texte exemple)
        test_embedding = self.embedder.generate_single("test")
        if test_embedding is not None:
            self.vector_size = len(test_embedding)
        
        self.ingestion = IngestionPipeline()
           
        # Initialisation du store
        self.vector_store = VectorStore(host="localhost",
                            port=6333,
                            sparse_model_name="Qdrant/bm25",  # ou "prithivida/Splade_PP_en_v1"
                            collection_name="documents",
                            vector_size=self.vector_size if self.vector_size else None
                        )
        
        # Initialisation de retrevier
        self.hybrid_retriever = HybridRetriever(self.vector_store)
        
        # MinIO client
        self.minio_client = MinIOService()
        
        # Créer la collection si nécessaire
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialise le vector store"""
        self.vector_store.create_collection()
    
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
            embeddings, chunks = self.ingestion.process_document(bucket=bucket,filename=filename)
            
            if embeddings and chunks :
                print(f"✅ Succès! {len(chunks)} chunks traités")
                print(f"   Dimensions embeddings: {len(embeddings[0]) if embeddings else 0}")
                
                # Utilisation des résultats
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    print(f"\nChunk {i+1}:")
                    print(f"  Texte: {chunk['text'][:50]}...")
                    print(f"  Métadonnées: {chunk['metadata']}")
                    print(f"  Embedding shape: {len(embedding)}")
                    
                # Stockage dans une base vectorielle (Indexer dans Qdrant)
                success = self.vector_store.index_documents(chunks, embeddings)
                logger.info(f"✅ Document '{filename}' traité avec succès !")
                if success:
                    logger.info(f"✅ Indexation du Document {filename} traité avec succès ")
                    return True
                else:
                    logger.error(f"❌ Échec indexation: {filename}")
                    return False
            else:
                logger.error(f"❌ Échec d'indexation du document '{filename}'")
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