"""
Router Recherche — SEINENTAI4US
POST /search          - Recherche sémantique dense
GET  /search/hybrid   - Recherche hybride (BM25 + dense)
"""

import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from seinentai4us_api.api.dependencies.auth import get_current_user
from seinentai4us_api.api.models.schemas import (
    HybridSearchResponse,
    RerankResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    UserProfile,
)
from seinentai4us_api.api.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_results(raw: list) -> list[SearchResult]:
    """Normalise les résultats bruts du retriever en objets SearchResult."""
    results = []
    for r in raw:
        meta = r.get("metadata", {})
        results.append(
            SearchResult(
                text=r.get("text", ""),
                filename=r.get("filename") or meta.get("filename", "inconnu"),
                score=float(r.get("score", 0.0)),
                chunk_index=r.get("chunk_index") or meta.get("chunk_index", 0),
                total_chunks=r.get("total_chunks") or meta.get("total_chunks"),
                doc_id=r.get("doc_id") or meta.get("doc_id"),
                metadata=meta,
            )
        )
    return results


# ─── Recherche sémantique ─────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SearchResponse,
    summary="Recherche sémantique (embeddings denses)",
)
async def semantic_search(
    body: SearchRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Effectue une recherche sémantique par similarité de vecteurs denses.

    - **query** : question ou phrase de recherche
    - **limit** : nombre maximum de résultats (1–50)
    - **score_threshold** : score minimal de similarité (0.0–1.0)
    - **filename_filter** : restreindre la recherche à un seul document
    - **use_hybrid** : Activer la recherche hybride (dense + sparse)
    - **use_hyde** : Active HyDE pour enrichir la requête dense
    """
    t0 = time.perf_counter()
    raw = rag_service.search(
        query=body.query,
        limit=body.limit,
        score_threshold=body.score_threshold,
        filename_filter=body.filename_filter,
        use_hybrid=body.use_hybrid,
        use_hyde=body.use_hyde,
    )
    elapsed = (time.perf_counter() - t0) * 1000

    results = _format_results(raw)
    return SearchResponse(
        query=body.query,
        results=results,
        total=len(results),
        search_time_ms=round(elapsed, 2),
    )


# ─── Recherche hybride ────────────────────────────────────────────────────────

@router.get(
    "/hybrid",
    response_model=HybridSearchResponse,
    summary="Recherche hybride (BM25 + embeddings denses)",
)
async def hybrid_search(
    q: str = Query(..., min_length=1, description="Texte de la requête"),
    limit: int = Query(5, ge=1, le=50),
    score_threshold: float = Query(0.0, ge=0.0, le=1.0),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Recherche hybride combinant :
    - Similarité sémantique (embeddings denses)
    - Correspondance lexicale (BM25 / sparse)

    Produit en général de meilleurs résultats que la recherche purement sémantique
    pour des requêtes avec des termes techniques ou des noms propres.
    """
    t0 = time.perf_counter()
    raw = rag_service.hybrid_search(query=q, limit=limit, score_threshold=score_threshold)
    elapsed = (time.perf_counter() - t0) * 1000

    results = _format_results(raw)
    return HybridSearchResponse(
        query=q,
        results=results,
        total=len(results),
        search_type="hybrid",
        search_time_ms=round(elapsed, 2),
    )


# ─── Recherche avec re-ranking ────────────────────────────────────────────────


