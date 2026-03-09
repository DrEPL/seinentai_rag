import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Génère des embeddings pour les chunks de texte"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle d'embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"🔄 Chargement du modèle {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Modèle chargé: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers non installé")
            raise
        except Exception as e:
            logger.error(f"Erreur chargement modèle: {e}")
            raise
    
    def generate(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Génère des embeddings pour une liste de textes
        
        Args:
            texts: Liste de textes
            batch_size: Taille des batchs pour le traitement
            
        Returns:
            Liste d'embeddings (vecteurs numpy)
        """
        if not texts:
            return []
        
        try:
            # Générer les embeddings par batch
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            logger.info(f"✅ {len(embeddings)} embeddings générés (dim={embeddings.shape[1]})")
            return list(embeddings)
            
        except Exception as e:
            logger.error(f"Erreur génération embeddings: {e}")
            return []
    
    def generate_single(self, text: str) -> Optional[np.ndarray]:
        """Génère un embedding pour un seul texte"""
        embeddings = self.generate([text])
        return embeddings[0] if embeddings else None


# class OllamaEmbeddingGenerator:
#     """Alternative avec Ollama pour des modèles locaux"""
    
#     def __init__(self, model_name: str = "nomic-embed-text", 
#                  host: str = "http://ollama:11434"):
#         self.model_name = model_name
#         self.host = host
#         self.client = None
#         self._init_client()
    
#     def _init_client(self):
#         try:
#             import ollama
#             self.client = ollama.Client(host=self.host)
#             logger.info(f"✅ Client Ollama connecté à {self.host}")
#         except ImportError:
#             logger.error("ollama non installé")
#             raise
    
#     def generate(self, texts: List[str]) -> List[np.ndarray]:
#         embeddings = []
#         for text in texts:
#             try:
#                 response = self.client.embeddings(
#                     model=self.model_name,
#                     prompt=text
#                 )
#                 embeddings.append(np.array(response['embedding']))
#             except Exception as e:
#                 logger.error(f"Erreur génération embedding: {e}")
#                 embeddings.append(np.zeros(768))  # Fallback
        
#         logger.info(f"✅ {len(embeddings)} embeddings générés (Ollama)")
#         return embeddings