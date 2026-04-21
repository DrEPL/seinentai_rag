"""
Agent Tools — Outils modulaires de retrieval pour l'agent RAG.

Chaque outil encapsule une stratégie de recherche spécifique
et est appelé dynamiquement par le graphe LangGraph.
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolResult:
    """Résultat standardisé d'un appel d'outil."""

    def __init__(
        self,
        tool_name: str,
        documents: List[Dict[str, Any]],
        execution_time: float,
        params: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None,
    ):
        self.tool_name = tool_name
        self.documents = documents
        self.execution_time = execution_time
        self.params = params
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "num_documents": len(self.documents),
            "execution_time_ms": round(self.execution_time * 1000, 1),
            "params": self.params,
            "success": self.success,
            "error": self.error,
        }

    def to_observation(self) -> str:
        """Formate le résultat en texte lisible par le LLM (Observation)."""
        if not self.success:
            return f"[{self.tool_name}] Échec: {self.error}"

        if not self.documents:
            return f"[{self.tool_name}] Aucun document pertinent trouvé."

        lines = [
            f"[{self.tool_name}] {len(self.documents)} documents trouvés "
            f"(en {self.execution_time * 1000:.0f}ms):"
        ]
        for i, doc in enumerate(self.documents[:5], 1):
            score = doc.get("score", 0.0)
            filename = doc.get("filename", "?")
            text_preview = doc.get("text", "")[:150].replace("\n", " ")
            lines.append(f"  {i}. [{filename}] (score={score:.3f}) {text_preview}...")

        if len(self.documents) > 5:
            lines.append(f"  ... et {len(self.documents) - 5} documents supplémentaires")

        return "\n".join(lines)


class RetrievalTools:
    """
    Ensemble d'outils de retrieval utilisés par l'agent.

    Encapsule le RetrieverPipeline existant et expose chaque stratégie
    comme un outil distinct avec des paramètres pré-configurés.
    """

    def __init__(self, retriever_pipeline):
        """
        Args:
            retriever_pipeline: Instance de RetrieverPipeline injectée.
        """
        self.retriever = retriever_pipeline

    def dense_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        candidate_limit: int = 30,
    ) -> ToolResult:
        """
        Recherche vectorielle dense (embeddings).

        Idéale pour les requêtes bien formulées et spécifiques.
        N'utilise ni HyDE ni BM25.
        """
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold,
            "use_hybrid": False,
            "use_hyde": False,
            "candidate_limit": candidate_limit,
        }
        logger.info(f"🔧 Tool dense_search: '{query[:80]}' limit={limit}")

        start = time.time()
        try:
            docs = self.retriever.search(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                use_hybrid=False,
                use_hyde=False,
                candidate_limit=candidate_limit,
            )
            elapsed = time.time() - start
            logger.info(f"🔧 dense_search → {len(docs)} docs en {elapsed*1000:.0f}ms")
            return ToolResult("dense_search", docs, elapsed, params)
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"🔧 dense_search ERREUR: {e}")
            return ToolResult("dense_search", [], elapsed, params, success=False, error=str(e))

    def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        candidate_limit: int = 30,
    ) -> ToolResult:
        """
        Recherche hybride Dense + BM25 (sparse).

        Idéale quand la requête contient des termes techniques,
        noms propres, acronymes ou mots-clés importants.
        """
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold,
            "use_hybrid": True,
            "use_hyde": False,
            "candidate_limit": candidate_limit,
        }
        logger.info(f"🔧 Tool hybrid_search: '{query[:80]}' limit={limit}")

        start = time.time()
        try:
            docs = self.retriever.search(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                use_hybrid=True,
                use_hyde=False,
                candidate_limit=candidate_limit,
            )
            elapsed = time.time() - start
            logger.info(f"🔧 hybrid_search → {len(docs)} docs en {elapsed*1000:.0f}ms")
            return ToolResult("hybrid_search", docs, elapsed, params)
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"🔧 hybrid_search ERREUR: {e}")
            return ToolResult("hybrid_search", [], elapsed, params, success=False, error=str(e))

    def hyde_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        hyde_alpha: float = 0.35,
        candidate_limit: int = 30,
    ) -> ToolResult:
        """
        Recherche HyDE (Hypothetical Document Embeddings).

        Génère un pseudo-document hypothétique puis effectue une recherche dense
        avec l'embedding fusionné. Idéale pour les requêtes conceptuelles ou abstraites.
        """
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold,
            "use_hybrid": False,
            "use_hyde": True,
            "hyde_alpha": hyde_alpha,
            "candidate_limit": candidate_limit,
        }
        logger.info(f"🔧 Tool hyde_search: '{query[:80]}' limit={limit}")

        start = time.time()
        try:
            docs = self.retriever.search(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                use_hybrid=False,
                use_hyde=True,
                hyde_alpha=hyde_alpha,
                candidate_limit=candidate_limit,
            )
            elapsed = time.time() - start
            logger.info(f"🔧 hyde_search → {len(docs)} docs en {elapsed*1000:.0f}ms")
            return ToolResult("hyde_search", docs, elapsed, params)
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"🔧 hyde_search ERREUR: {e}")
            return ToolResult("hyde_search", [], elapsed, params, success=False, error=str(e))

    def rerank_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> ToolResult:
        """
        Reranking cross-encoder sur un ensemble de documents.

        Applique un modèle cross-encoder pour reclasser les documents
        par pertinence fine par rapport à la requête.
        """
        params = {"query": query, "top_k": top_k, "input_docs": len(documents)}
        logger.info(f"🔧 Tool rerank: {len(documents)} docs → top_k={top_k}")

        start = time.time()
        try:
            if self.retriever.reranker is None:
                # Fallback: trier par score existant
                sorted_docs = sorted(
                    documents, key=lambda d: d.get("score", 0.0), reverse=True
                )
                elapsed = time.time() - start
                return ToolResult("rerank", sorted_docs[:top_k], elapsed, params)

            reranked = self.retriever.reranker.rerank(query, documents, top_k=top_k)
            elapsed = time.time() - start
            logger.info(f"🔧 rerank → {len(reranked)} docs en {elapsed*1000:.0f}ms")
            return ToolResult("rerank", reranked, elapsed, params)
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"🔧 rerank ERREUR: {e}")
            return ToolResult("rerank", documents[:top_k], elapsed, params, success=False, error=str(e))

    def execute(self, strategy: str, query: str, **kwargs) -> ToolResult:
        """
        Exécute l'outil de recherche correspondant à la stratégie.

        Args:
            strategy: "dense" | "hybrid" | "hyde"
            query: Requête de recherche
            **kwargs: Paramètres supplémentaires

        Returns:
            ToolResult standardisé
        """
        # Normalisation de la stratégie (ex: "hyde_search" -> "hyde")
        normalized_strategy = strategy.replace("_search", "").strip().lower()
        
        tool_map = {
            "dense": self.dense_search,
            "hybrid": self.hybrid_search,
            "hyde": self.hyde_search,
        }

        tool_fn = tool_map.get(normalized_strategy)
        if tool_fn is None:
            return ToolResult(
                f"unknown_{strategy}", [], 0.0, {"strategy": strategy},
                success=False, error=f"Stratégie inconnue: {strategy}",
            )

        return tool_fn(query=query, **kwargs)
