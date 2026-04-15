import logging
from typing import Any, List, Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    """Reranker cross-encoder pour reclasser les petits chunks."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2",
                 device: Optional[str] = None, batch_size: int = 32):
        """
        Args:
            model_name: Nom du modèle cross-encoder
            device: 'cpu', 'cuda' ou None (auto)
            batch_size: Taille des batchs pour le scoring
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.model = None
        
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name, device=device)
            logger.info(f"✅ Cross-encoder chargé: {self.model_name} sur {self.model.device}")
        except Exception as e:
            logger.warning(f"⚠️ Cross-encoder non disponible ({self.model_name}): {e}")

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Reclasse les documents par pertinence avec le cross-encoder.
        
        Args:
            query: Requête de recherche
            docs: Liste de documents avec leur score original
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste reclassée des top_k documents
        """
        if not docs or not query:
            return docs[:top_k] if docs else []
        
        # Fallback si modèle non disponible
        if self.model is None:
            logger.debug("Fallback: tri par score original")
            sorted_docs = sorted(docs, key=lambda d: d.get("score", 0.0), reverse=True)
            return sorted_docs[:top_k]
        
        # Préparation des paires (query, document)
        pairs = [(query, doc.get("text", "")) for doc in docs]
        
        # Scoring par batch pour éviter les OOM
        all_scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i:i + self.batch_size]
            batch_scores = self.model.predict(batch)
            all_scores.extend(batch_scores)
        
        # Construction des résultats avec conservation du score original
        reranked = []
        for doc, score in zip(docs, all_scores):
            updated = doc.copy()  # Évite de modifier l'original
            updated["retrieval_score"] = doc.get("score", 0.0)
            updated["score"] = float(score)
            updated["reranked"] = True
            updated["reranker"] = self.model_name
            reranked.append(updated)
        
        # Tri par nouveau score (descendant)
        reranked.sort(key=lambda d: d.get("score", 0.0), reverse=True)
        
        logger.debug(f"Reranking terminé: {len(docs)} → {top_k} documents")
        return reranked[:top_k]