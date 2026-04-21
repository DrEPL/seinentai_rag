"""
Agent State — Définition du state LangGraph pour le RAG agentique.

Ce TypedDict décrit l'état complet qui circule entre les nœuds du graphe.
Chaque nœud lit et écrit dans ce state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """State partagé entre tous les nœuds du graphe LangGraph."""

    # ── Entrée ────────────────────────────────────────────────────────────────
    query: str                          # Requête originale de l'utilisateur
    conversation_context: str           # Contexte conversationnel (chat continu)

    # ── Analyse de la requête ─────────────────────────────────────────────────
    query_type: str                     # simple | complex | multi_hop | ambiguous | out_of_domain
    search_strategy: str                # dense | hybrid | hyde
    reasoning: str                      # Justification du choix de l'agent

    # ── Décomposition (questions complexes) ───────────────────────────────────
    sub_queries: List[str]              # Sous-requêtes décomposées
    current_sub_query_index: int        # Index de la sous-requête en cours
    sub_query_results: List[List[Dict[str, Any]]]  # Résultats par sous-requête

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_docs: List[Dict[str, Any]]    # Documents récupérés (cumulés)
    reranked_docs: List[Dict[str, Any]]     # Documents après reranking

    # ── Évaluation de la qualité ──────────────────────────────────────────────
    quality_score: float                # Score de qualité évalué (0.0 - 1.0)
    quality_sufficient: bool            # Qualité suffisante pour la synthèse ?
    quality_feedback: str               # Explication de l'évaluation

    # ── Boucle de contrôle ────────────────────────────────────────────────────
    iteration: int                      # Itération courante
    max_iterations: int                 # Limite de sécurité (défaut: 4)
    strategies_tried: List[str]         # Stratégies déjà essayées

    # ── Traçabilité (pour le streaming SSE) ───────────────────────────────────
    thoughts: List[Dict[str, Any]]      # Journal de raisonnement de l'agent
    tool_calls_log: List[Dict[str, Any]]  # Journal des appels aux outils

    # ── Sortie ────────────────────────────────────────────────────────────────
    final_response: str                 # Réponse finale synthétisée
    sources: List[Dict[str, Any]]       # Sources utilisées dans la réponse
    error: Optional[str]                # Message d'erreur éventuel
