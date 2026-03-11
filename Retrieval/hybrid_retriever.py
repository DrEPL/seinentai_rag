import logging
import numpy as np
from typing import List, Dict, Any, Optional
from vector_store import VectorStore

logger = logging.getLogger(__name__)

class HybridRetriever:
    """Retriever hybride utilisant VectorStore"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def retrieve(self,
                query_text: str,
                query_embedding: np.ndarray,
                sparse_vector: Optional[Dict] = None,
                limit: int = 5,
                use_hybrid: bool = True,
                score_threshold: float = 0.2,
                filter_condition: Optional[Dict] = None) -> List[Dict]:
        """
        Méthode principale de retrieval
        
        Args:
            query_text: Texte de la requête (pour générer le sparse vector)
            query_embedding: Vecteur dense
            sparse_vector: Vecteur sparse optionnel
            limit: Nombre de résultats
            score_threshold: Seuil de score minimal entre 0.0 et 1.0
            use_hybrid: True = recherche hybride, False = dense only
            filter_condition: Filtres optionnels (ex: {"filename": "doc.pdf"})
        """
        if use_hybrid and sparse_vector:
            # Recherche hybride
            results = self.vector_store.hybrid_search(
                query_text=query_text,
                query_embedding=query_embedding,
                sparse_vector=sparse_vector,
                limit=limit,
                score_threshold=score_threshold,
                filter_condition=filter_condition
            )
        else:
            # Recherche dense uniquement
            results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit,
                filter_condition=filter_condition,
                score_threshold=score_threshold
            )
        
        return results