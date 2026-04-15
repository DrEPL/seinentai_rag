import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
from Ingestion.ingestion_pipeline import IngestionPipeline
from Retrieval.HyDEGenerator import HyDEGenerator
from Retrieval.cross_encoder_reranker import CrossEncoderReranker
from Retrieval.hybrid_retriever import HybridRetriever
from services.minio_service import MinIOService
from Retrieval.vector_store import VectorStore
from Ingestion.embeddings import EmbeddingGenerator
from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

class RetrieverPipeline:
    """Pipeline Retriever"""
    
    def __init__(
        self,
        embedder: Optional[EmbeddingGenerator] = None,
        ingestion: Optional[IngestionPipeline] = None,
        vector_store: Optional[VectorStore] = None,
        minio_client: Optional[MinIOService] = None,
        hyde_generator: Optional[HyDEGenerator] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        # Injecter les dépendances pour éviter la recréation (modèle embeddings / client MinIO / connexion Qdrant).
        self.minio_client = minio_client or MinIOService()

        if embedder is None:
            embedder = EmbeddingGenerator(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'))

        self.embedder = embedder
        logger.info(
            "⚙️ Initialisation RetrieverPipeline",
            extra={
                "embedder": "provided" if embedder is not None else "default",
                "vector_store": "provided" if vector_store is not None else "default",
                "minio_client": "provided" if minio_client is not None else "default",
            },
        )

        if vector_store is None:
            # Obtenir la dimension du modèle (test avec un texte exemple)
            test_embedding = self.embedder.generate_single("test")
            vector_size = len(test_embedding) if test_embedding is not None else 384

            # Initialisation du store (fallback si pas injecté)
            vector_store = VectorStore(
                host="localhost",
                port=6333,
                sparse_model_name="Qdrant/bm25",
                collection_name="documents",
                vector_size=vector_size,
            )

        self.vector_store = vector_store

        # Pipeline ingestion (chunking + embeddings côté indexation)
        if ingestion is None:
            ingestion = IngestionPipeline(
                embedder=self.embedder,
                minio_client=self.minio_client,
                vector_store=self.vector_store,
            )
        self.ingestion = ingestion

        # Initialisation de retriever
        self.hybrid_retriever = HybridRetriever(self.vector_store)
        self.hyde_generator = hyde_generator or HyDEGenerator()
        self.reranker = reranker or CrossEncoderReranker()

        # Créer la collection si nécessaire (une seule fois via singleton)
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
            embeddings, chunks, doc_id = self.ingestion.process_document(bucket=bucket,filename=filename)
            
            if embeddings and chunks :
                # Stockage dans une base vectorielle (Indexer dans Qdrant)
                success = self.vector_store.index_documents(chunks, embeddings, doc_id=doc_id)
                logger.info(f"✅ Document '{filename}' traité avec succès !")
                if success:
                    logger.info(f"✅ Indexation du Document {filename} traité avec succès ")
                    return True
                else:
                    logger.error(f"❌ Échec indexation du document: {filename}")
                    return False
            else:
                logger.error(f"⏭️ Document ignoré (déjà indexé): {filename}")
                return True   
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement {filename}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def _fuse_query_embeddings(query_embedding: np.ndarray, hyde_embedding: np.ndarray, hyde_alpha: float) -> np.ndarray:
        alpha = max(0.0, min(1.0, hyde_alpha))
        fused = ((1.0 - alpha) * query_embedding) + (alpha * hyde_embedding)
        norm = np.linalg.norm(fused)
        return fused / norm if norm > 0 else fused

    @staticmethod
    def _parent_dedup_key(chunk: Dict[str, Any]) -> str:
        metadata = chunk.get("metadata", {})
        doc_id = chunk.get("doc_id", "") or metadata.get("doc_id", "")
        parent_chunk_id = metadata.get("parent_chunk_id") or chunk.get("parent_chunk_id")
        if parent_chunk_id:
            return f"{doc_id}::{parent_chunk_id}"

        # Fallback robuste pour données anciennes: texte parent normalisé
        parent_text = (
            metadata.get("parent_chunk_text")
            or metadata.get("parent_text")
            or chunk.get("parent_chunk_text")
            or chunk.get("parent_text")
            or chunk.get("text", "")
        )
        normalized = " ".join(parent_text.split()).strip().lower()
        return f"{doc_id}::text::{normalized[:500]}"

    @staticmethod
    def _lift_to_parent_paragraphs(reranked_small_chunks: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        parent_map: Dict[str, Dict[str, Any]] = {}
        parent_order: List[str] = []

        # Parcours dans l'ordre reranké: dès qu'un parent est déjà vu, on saute au chunk suivant.
        for chunk in reranked_small_chunks:
            metadata = chunk.get("metadata", {})
            parent_chunk_id = metadata.get("parent_chunk_id") or chunk.get("parent_chunk_id")
            if not parent_chunk_id:
                parent_chunk_id = f"{chunk.get('doc_id', 'unknown')}:{chunk.get('chunk_index', 0)}"

            parent_text = (
                metadata.get("parent_chunk_text")
                or chunk.get("parent_chunk_text")
                or chunk.get("text", "")
            )
            if not parent_chunk_id:
                continue

            dedup_key = RetrieverPipeline._parent_dedup_key(chunk)
            best_existing = parent_map.get(dedup_key)
            candidate_score = float(chunk.get("score", 0.0))
            if best_existing is None:
                parent_order.append(dedup_key)
                parent_map[dedup_key] = {
                    "parent_chunk_id": parent_chunk_id,
                    "doc_id": chunk.get("doc_id", ""),
                    "filename": chunk.get("filename", ""),
                    "text": parent_text,
                    "score": candidate_score,
                    "metadata": {
                        **metadata,
                        "small_chunks": [{
                            "id": chunk.get("id"),
                            "chunk_index": chunk.get("chunk_index"),
                            "score": candidate_score,
                            "text": chunk.get("text", ""),
                        }]
                    },
                }
                if len(parent_order) >= limit:
                    break
            else:
                best_existing["metadata"]["small_chunks"].append({
                    "id": chunk.get("id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "score": candidate_score,
                    "text": chunk.get("text", ""),
                })

        return [parent_map[key] for key in parent_order]

    def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        use_hybrid: bool = True,
        use_hyde: bool = False,
        hyde_alpha: float = 0.35,
        candidate_limit: int = 30,
        rerank_top_k: Optional[int] = None,
        small_to_big: bool = True,
    ) -> list:
        """
        Recherche des documents similaires à une requête
        
        Args:
            query: Texte de la requête
            limit: Nombre de résultats
            score_threshold: Seuil de score minimal entre 0.0 et 1.0
            use_hybrid: True = recherche hybride, False = dense only
            use_hyde: Active HyDE pour enrichir la requête dense
            hyde_alpha: Pondération de l'embedding HyDE dans la fusion
            candidate_limit: Nombre de candidats small chunks avant rerank
            rerank_top_k: Nombre de small chunks conservés après rerank (par défaut = limit)
            small_to_big: Retourne des paragraphes parents uniques après rerank
            
        Returns:
            Liste des documents pertinents
        """
        logger.info(
            f"🔎 Recherche query='{query[:100]}' limit={limit} use_hybrid={use_hybrid} use_hyde={use_hyde} "
            f"candidate_limit={candidate_limit} rerank_top_k={rerank_top_k} small_to_big={small_to_big}"
        )

        # 1) Embedding dense de la requête originale
        query_embedding = self.embedder.generate_single(query)
        if query_embedding is None:
            logger.error("❌ Impossible de générer l'embedding de la requête")
            return []

        # 2) Optionnel: HyDE (générer un pseudo-document puis fusionner les embeddings)
        if use_hyde and self.hyde_generator is not None:
            hypothetical_doc = self.hyde_generator.generate(query)
            logger.info(f"HyDE généré: {hypothetical_doc[:120] if hypothetical_doc else 'aucun contenu'}")
            if hypothetical_doc:
                hyde_embedding = self.embedder.generate_single(hypothetical_doc)
                if hyde_embedding is not None:
                    query_embedding = self._fuse_query_embeddings(query_embedding, hyde_embedding, hyde_alpha)
                    logger.info("Embeddings HyDE fusionnés avec succès")
                else:
                    logger.warning("⚠️ Embedding HyDE introuvable, utilisation de l'embedding original")

        # 3) Candidate retrieval (small chunks)
        effective_candidate_limit = max(candidate_limit, limit)
        candidates = self.hybrid_retriever.retrieve(
            query_text=query,
            query_embedding=query_embedding,
            limit=effective_candidate_limit,
            score_threshold=score_threshold,
            use_hybrid=use_hybrid,
        )
        logger.info(f"Nombre de candidats récupérés: {len(candidates) if candidates is not None else 0}")
        if not candidates:
            logger.info("⚠️ Aucun candidat trouvé pour la requête")
            return []

        # 4) Cross-encoder reranking des small chunks
        # Pour small-to-big, on rerank un pool plus large afin d'obtenir assez de parents uniques.
        rerank_size = rerank_top_k if rerank_top_k is not None else (effective_candidate_limit if small_to_big else limit)
        rerank_size = max(1, rerank_size)
        logger.info(f"Reranking top_k={rerank_size}")
        top_small_chunks = self.reranker.rerank(query, candidates, top_k=rerank_size) if self.reranker else candidates[:rerank_size]

        # 5) Small-to-big: remonter vers paragraphes parents uniques après reranking
        if small_to_big:
            parent_paragraphs = self._lift_to_parent_paragraphs(top_small_chunks, limit=limit)
            logger.info(f"Parent paragraphs générés: {len(parent_paragraphs)}")
            final_results = parent_paragraphs
        else:
            final_results = top_small_chunks[:limit]

        logger.info(f"🔍 {len(final_results)} résultats pour: '{query[:50]}...'")
        return final_results
