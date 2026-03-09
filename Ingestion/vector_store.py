import logging
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class VectorStore:
    """Stockage vectoriel avec Qdrant"""
    
    def __init__(self, host: str = "qdrant", port: int = 6333, 
                 collection_name: str = "documents"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self._connect()
    
    def _connect(self):
        """Établit la connexion à Qdrant"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            # Tester la connexion
            self.client.get_collections()
            logger.info(f"✅ Connecté à Qdrant {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Qdrant: {e}")
            raise
    
    def create_collection(self, vector_size: int = 384, distance: Distance = Distance.COSINE):
        """Crée la collection si elle n'existe pas"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance)
                )
                logger.info(f"✅ Collection '{self.collection_name}' créée")
            else:
                logger.info(f"ℹ Collection '{self.collection_name}' existe déjà")
                
        except Exception as e:
            logger.error(f"❌ Erreur création collection: {e}")
    
    def index_documents(self, chunks: List[Dict[str, Any]], 
                       embeddings: List[np.ndarray]) -> bool:
        """
        Indexe des chunks avec leurs embeddings
        
        Args:
            chunks: Liste de chunks avec métadonnées
            embeddings: Liste d'embeddings correspondants
            
        Returns:
            True si succès
        """
        if len(chunks) != len(embeddings):
            logger.error("Nombre de chunks et d'embeddings différent")
            return False
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Créer un ID unique
            point_id = str(uuid.uuid4())
            
            # Préparer les métadonnées
            payload = {
                'text': chunk['text'],
                'doc_id': chunk.get('doc_id', 'unknown'),
                'filename': chunk.get('filename', 'unknown'),
                'chunk_index': chunk.get('chunk_index', i),
                'total_chunks': chunk.get('total_chunks', 1),
                'metadata': chunk.get('metadata', {})
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=payload
            ))
        
        try:
            # Upload par batch
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            logger.info(f"✅ {len(points)} documents indexés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur indexation: {e}")
            return False
    
    def search(self, query_embedding: np.ndarray, limit: int = 5) -> List[Dict]:
        """Recherche les documents similaires"""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit
            )
            
            return [
                {
                    'id': hit.id,
                    'score': hit.score,
                    'text': hit.payload.get('text', ''),
                    'filename': hit.payload.get('filename', ''),
                    'metadata': hit.payload
                }
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Supprime tous les chunks d'un document"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_id",
                            match=models.MatchValue(value=doc_id)
                        )
                    ]
                )
            )
            logger.info(f"✅ Document {doc_id} supprimé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur suppression: {e}")
            return False