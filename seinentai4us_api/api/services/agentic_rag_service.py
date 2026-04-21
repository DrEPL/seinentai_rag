"""
Agentic RAG Service — SEINENTAI4US

Service haut-niveau qui orchestre l'agent LangGraph.
Fournit des méthodes synchrones et streaming (SSE) pour l'API.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Tuple
from Agent.graph import build_agent_graph
from Agent.state import AgentState
from Agent.tools import RetrievalTools

logger = logging.getLogger(__name__)

# ── Lazy singleton ────────────────────────────────────────────────────────────
_agentic_service = None


def get_agentic_service() -> "AgenticRAGService":
    """Retourne le singleton du service agentique."""
    global _agentic_service
    if _agentic_service is None:
        raise RuntimeError(
            "AgenticRAGService non initialisé. "
            "Appelez initialize_agentic_service() au démarrage."
        )
    return _agentic_service


def initialize_agentic_service(retriever_pipeline) -> "AgenticRAGService":
    """
    Initialise le singleton AgenticRAGService.

    Args:
        retriever_pipeline: Instance de RetrieverPipeline.

    Returns:
        L'instance initialisée.
    """
    global _agentic_service
    _agentic_service = AgenticRAGService(retriever_pipeline)
    logger.info("🤖 AgenticRAGService initialisé")
    return _agentic_service


class AgenticRAGService:
    """
    Façade pour l'exécution du graphe LangGraph RAG agentique.

    Fournit :
    - `run()` : Exécution complète, retourne la réponse finale
    - `stream()` : Générateur synchrone d'événements SSE (thoughts, tool_calls, tokens)
    """

    def __init__(self, retriever_pipeline):
        self.tools = RetrievalTools(retriever_pipeline)
        self.graph = build_agent_graph(self.tools)
        logger.info("🤖 Agent graph compilé")

    def _build_initial_state(
        self,
        query: str,
        conversation_context: str = "",
        max_iterations: int = 4,
    ) -> AgentState:
        """Construit l'état initial pour une exécution du graphe."""
        return AgentState(
            query=query,
            conversation_context=conversation_context,
            query_type="",
            search_strategy="",
            reasoning="",
            sub_queries=[],
            current_sub_query_index=0,
            sub_query_results=[],
            retrieved_docs=[],
            reranked_docs=[],
            quality_score=0.0,
            quality_sufficient=False,
            quality_feedback="",
            iteration=0,
            max_iterations=max_iterations,
            strategies_tried=[],
            thoughts=[],
            tool_calls_log=[],
            final_response="",
            sources=[],
            error=None,
        )

    # ── Exécution complète ────────────────────────────────────────────────────

    def run(
        self,
        query: str,
        conversation_context: str = "",
        max_iterations: int = 4,
    ) -> Dict[str, Any]:
        """
        Exécute l'agent et retourne la réponse finale.

        Args:
            query: Requête de l'utilisateur.
            conversation_context: Contexte conversationnel (messages précédents).
            max_iterations: Nombre max d'itérations de fallback.

        Returns:
            Dict avec : response, sources, agent_trace, model, generation_time, success
        """
        start_time = time.time()
        initial_state = self._build_initial_state(query, conversation_context, max_iterations)

        try:
            # Exécuter le graphe
            final_state = self.graph.invoke(initial_state)

            generation_time = time.time() - start_time

            return {
                "success": True,
                "response": final_state.get("final_response", ""),
                "sources": final_state.get("sources", []),
                "model": "agent-langgraph",
                "generation_time": generation_time,
                "agent_trace": {
                    "query_type": final_state.get("query_type", ""),
                    "strategies_tried": final_state.get("strategies_tried", []),
                    "iterations": final_state.get("iteration", 0),
                    "quality_score": final_state.get("quality_score", 0.0),
                    "thoughts": final_state.get("thoughts", []),
                    "tool_calls": final_state.get("tool_calls_log", []),
                    "sub_queries": final_state.get("sub_queries", []),
                },
            }

        except Exception as e:
            logger.error(f"❌ Agent execution error: {e}", exc_info=True)
            generation_time = time.time() - start_time
            return {
                "success": False,
                "response": None,
                "error": str(e),
                "model": "agent-langgraph",
                "generation_time": generation_time,
                "agent_trace": {
                    "thoughts": initial_state.get("thoughts", []),
                    "tool_calls": initial_state.get("tool_calls_log", []),
                },
            }

    # ── Streaming SSE ─────────────────────────────────────────────────────────

    def stream(
        self,
        query: str,
        conversation_context: str = "",
        max_iterations: int = 4,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Exécute l'agent nœud par nœud et yield des événements SSE.

        Événements émis :
        - {"type": "thought", "node": "...", "content": "..."}
        - {"type": "tool_call", "tool": "...", "params": {...}, "result": "..."}
        - {"type": "observation", "content": "..."}
        - {"type": "synthesis_start"}
        - {"type": "response", "content": "..."}
        - {"type": "done", "agent_trace": {...}, "sources": [...]}
        - {"type": "error", "message": "..."}
        """
        initial_state = self._build_initial_state(query, conversation_context, max_iterations)
        start_time = time.time()

        try:
            # Utiliser stream_mode pour capturer l'état après chaque nœud
            prev_thoughts_count = 0
            prev_tool_calls_count = 0
            final_state = initial_state

            for event in self.graph.stream(initial_state, stream_mode="updates"):
                # event est un dict {node_name: state_update}
                for node_name, state_update in event.items():
                    if not isinstance(state_update, dict):
                        continue

                    # Émettre les nouvelles pensées
                    new_thoughts = state_update.get("thoughts", [])
                    for thought in new_thoughts[prev_thoughts_count:]:
                        yield {
                            "type": "thought",
                            "node": thought.get("node", node_name),
                            "content": thought.get("content", ""),
                            "timestamp": thought.get("timestamp", datetime.utcnow().isoformat()),
                        }
                    prev_thoughts_count = len(new_thoughts)

                    # Émettre les nouveaux appels d'outils
                    new_tool_calls = state_update.get("tool_calls_log", [])
                    for tc in new_tool_calls[prev_tool_calls_count:]:
                        yield {
                            "type": "tool_call",
                            "tool": tc.get("tool", ""),
                            "params": tc.get("params", {}),
                            "result": tc.get("result", ""),
                            "timestamp": tc.get("timestamp", datetime.utcnow().isoformat()),
                        }
                    prev_tool_calls_count = len(new_tool_calls)

                    # Capturer l'évaluation qualité
                    if "quality_score" in state_update and node_name == "evaluate_quality":
                        yield {
                            "type": "observation",
                            "content": (
                                f"Qualité: {state_update.get('quality_score', 0):.2f} — "
                                f"{'✅ Suffisant' if state_update.get('quality_sufficient') else '⚠️ Insuffisant'} — "
                                f"{state_update.get('quality_feedback', '')}"
                            ),
                        }

                    # Capturer la réponse finale
                    if "final_response" in state_update and state_update["final_response"]:
                        yield {"type": "synthesis_start"}
                        yield {
                            "type": "response",
                            "content": state_update["final_response"],
                        }

                    # Mettre à jour le state final
                    final_state = {**final_state, **state_update}

            # Événement de fin
            generation_time = time.time() - start_time
            yield {
                "type": "done",
                "generation_time": generation_time,
                "sources": final_state.get("sources", []),
                "agent_trace": {
                    "query_type": final_state.get("query_type", ""),
                    "strategies_tried": final_state.get("strategies_tried", []),
                    "iterations": final_state.get("iteration", 0),
                    "quality_score": final_state.get("quality_score", 0.0),
                    "thoughts": final_state.get("thoughts", []),
                    "tool_calls": final_state.get("tool_calls_log", []),
                },
            }

        except Exception as e:
            logger.error(f"❌ Agent stream error: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e),
            }
