"""
Agent Graph — Définition du StateGraph LangGraph pour le RAG agentique.

Ce module construit le graphe d'exécution de l'agent :
  analyze_query → (decompose_query | execute_search)
  → rerank_results → evaluate_quality
  → (synthesize_response | handle_fallback → execute_search)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from Agent.prompts import (
    FALLBACK_STRATEGY_PROMPT,
    QUALITY_EVALUATOR_PROMPT,
    QUERY_ANALYZER_PROMPT,
    QUERY_DECOMPOSER_PROMPT,
    SYNTHESIS_PROMPT,
)
from Agent.state import AgentState
from Agent.tools import RetrievalTools

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────
DEFAULT_MAX_ITERATIONS = 4
QUALITY_THRESHOLD = 0.6


# ── Helper LLM ───────────────────────────────────────────────────────────────

def _call_llm(prompt: str, system: str = "", temperature: float = 0.1, max_tokens: int = 1024) -> str:
    """Appelle le LLM via Ollama et retourne le texte brut."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL_NAME", "mistral-large-3:675b-cloud")

    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if system:
        body["system"] = system

    try:
        resp = requests.post(f"{base_url}/api/generate", json=body, timeout=120)
        if resp.status_code != 200:
            logger.error(f"LLM error {resp.status_code}: {resp.text[:300]}")
            return ""
        return resp.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ""


def _call_llm_stream(prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 2048):
    """Appelle le LLM via Ollama en mode streaming et yield les tokens."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL_NAME", "mistral-large-3:675b-cloud")

    body = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if system:
        body["system"] = system

    try:
        with requests.post(f"{base_url}/api/generate", json=body, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    decoded = json.loads(line.decode("utf-8"))
                    token = decoded.get("response", "")
                    if token:
                        yield token
                    if decoded.get("done"):
                        break
    except Exception as e:
        logger.error(f"LLM stream call failed: {e}")
        yield ""


def _parse_json_response(text: str) -> Dict[str, Any]:
    """Extrait le premier bloc JSON d'une réponse LLM."""
    # Tenter le parsing direct
    print(f"\n\n\n*********** DEBUG: Resultat LLM dans parse_json_response: ", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Chercher un bloc ```json ... ```
    import re
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Chercher le premier { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # Tentative de réparation (JSON tronqué)
    text_clean = text.strip()
    if match:
        text_clean = match.group(1).strip()
    elif start != -1:
        text_clean = text[start:]

    for suffix in ['"}', '"]}', '}', ']', '"]']:
        try:
            return json.loads(text_clean + suffix)
        except json.JSONDecodeError:
            continue

    logger.warning(f"Impossible de parser le JSON LLM: {text[:200]}")
    return {}


def _call_llm_json(prompt: str, temperature: float = 0.1, max_tokens: int = 1024, max_retries: int = 3) -> Dict[str, Any]:
    """Appelle le LLM et force un retour JSON valide avec un mécanisme de retry explicite."""
    for attempt in range(max_retries):
        raw = _call_llm(prompt, temperature=temperature, max_tokens=max_tokens)
        if not raw:
            delay = 2 ** attempt  # Backoff exponentiel : 1s, 2s, 4s
            logger.warning(f"LLM a retourné vide à la tentative {attempt+1}/{max_retries}. Attente de {delay}s.")
            time.sleep(delay)
            continue
            
        parsed = _parse_json_response(raw)
        if parsed:
            return parsed
            
        logger.warning(f"Échec du parsing JSON à la tentative {attempt+1}/{max_retries}")
        time.sleep(1)
        
    logger.error("Toutes les tentatives de génération JSON ont échoué.")
    return {}


def _add_thought(state: AgentState, node: str, content: str) -> None:
    """Ajoute une pensée au journal de traçabilité."""
    thoughts = list(state.get("thoughts", []))
    thoughts.append({
        "node": node,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    })
    state["thoughts"] = thoughts


def _add_tool_call(state: AgentState, tool_name: str, params: Dict, result_summary: str) -> None:
    """Ajoute un appel d'outil au journal."""
    log = list(state.get("tool_calls_log", []))
    log.append({
        "tool": tool_name,
        "params": params,
        "result": result_summary,
        "timestamp": datetime.utcnow().isoformat(),
    })
    state["tool_calls_log"] = log


# ── Nœuds du graphe ──────────────────────────────────────────────────────────

def analyze_query(state: AgentState) -> AgentState:
    """Nœud 1: Analyse la requête et détermine la stratégie de recherche."""
    query = state["query"]
    logger.info(f"📊 [analyze_query] Analyse de: '{query[:80]}'")

    prompt = QUERY_ANALYZER_PROMPT.format(query=query)
    parsed = _call_llm_json(prompt, temperature=0.1, max_tokens=512, max_retries=3)

    query_type = parsed.get("query_type", "simple")
    strategy = parsed.get("search_strategy", "dense")
    reasoning = parsed.get("reasoning", "Analyse par défaut")
    needs_decomposition = parsed.get("needs_decomposition", False)
    sub_queries = parsed.get("sub_queries", [])

    _add_thought(state, "analyze_query", (
        f"Type: {query_type} | Stratégie: {strategy} | "
        f"Décomposition: {needs_decomposition} | Raison: {reasoning}"
    ))

    state["query_type"] = query_type
    state["search_strategy"] = strategy
    state["reasoning"] = reasoning
    state["sub_queries"] = sub_queries if needs_decomposition else []
    state["current_sub_query_index"] = 0
    state["sub_query_results"] = []
    state["iteration"] = state.get("iteration", 0)
    state["max_iterations"] = state.get("max_iterations", DEFAULT_MAX_ITERATIONS)
    state["strategies_tried"] = list(state.get("strategies_tried", []))
    state["retrieved_docs"] = list(state.get("retrieved_docs", []))
    state["thoughts"] = list(state.get("thoughts", []))
    state["tool_calls_log"] = list(state.get("tool_calls_log", []))

    logger.info(f"📊 [analyze_query] → type={query_type} strategy={strategy} decompose={needs_decomposition}")
    return state


def decompose_query(state: AgentState) -> AgentState:
    """Nœud 2: Décompose une requête complexe en sous-requêtes."""
    query = state["query"]
    logger.info(f"🔀 [decompose_query] Décomposition de: '{query[:80]}'")

    # Si l'analyseur a déjà fourni des sous-requêtes, les utiliser
    if state.get("sub_queries"):
        _add_thought(state, "decompose_query",
                     f"Sous-requêtes déjà identifiées: {state['sub_queries']}")
        return state

    prompt = QUERY_DECOMPOSER_PROMPT.format(query=query)
    parsed = _call_llm_json(prompt, temperature=0.1, max_tokens=512, max_retries=3)

    sub_queries = parsed.get("sub_queries", [query])
    if sub_queries is None:
        sub_queries = [query]
    reasoning = parsed.get("reasoning", "")

    # Limiter à 4 sous-requêtes
    sub_queries = sub_queries[:4]

    _add_thought(state, "decompose_query",
                 f"{len(sub_queries)} sous-requêtes: {sub_queries} | {reasoning}")

    state["sub_queries"] = sub_queries
    state["current_sub_query_index"] = 0
    state["sub_query_results"] = []

    logger.info(f"🔀 [decompose_query] → {len(sub_queries)} sous-requêtes")
    return state


def execute_search(state: AgentState) -> AgentState:
    """Nœud 3: Exécute la recherche avec la stratégie choisie."""
    strategy = state.get("search_strategy", "dense")
    sub_queries = state.get("sub_queries", [])
    query = state["query"]

    # Track strategy
    tried = list(state.get("strategies_tried", []))
    if strategy not in tried:
        tried.append(strategy)
    state["strategies_tried"] = tried

    # Incrémenter l'itération
    state["iteration"] = state.get("iteration", 0) + 1

    # Récupérer les outils (injectés via le graph builder)
    tools: RetrievalTools = state.get("_tools")  # type: ignore[assignment]
    if tools is None:
        state["error"] = "Tools non initialisés"
        _add_thought(state, "execute_search", "❌ RetrievalTools non disponibles")
        return state

    all_docs: List[Dict[str, Any]] = list(state.get("retrieved_docs", []))

    if sub_queries:
        # Exécuter chaque sous-requête
        idx = state.get("current_sub_query_index", 0)
        sub_results = list(state.get("sub_query_results", []))

        for i, sq in enumerate(sub_queries[idx:], start=idx):
            _add_thought(state, "execute_search",
                         f"Sous-requête {i+1}/{len(sub_queries)}: '{sq}' → {strategy}")

            result = tools.execute(strategy, sq, limit=8)
            _add_tool_call(state, result.tool_name, result.params, result.to_observation())

            sub_results.append(result.documents)
            all_docs.extend(result.documents)

        state["sub_query_results"] = sub_results
        state["current_sub_query_index"] = len(sub_queries)
    else:
        # Requête simple
        _add_thought(state, "execute_search", f"Recherche '{strategy}' pour: '{query[:80]}'")

        result = tools.execute(strategy, query, limit=10)
        _add_tool_call(state, result.tool_name, result.params, result.to_observation())

        all_docs.extend(result.documents)

    # Dédupliquer les documents par texte
    seen_texts = set()
    unique_docs = []
    for doc in all_docs:
        text_key = doc.get("text", "")[:200]
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_docs.append(doc)

    state["retrieved_docs"] = unique_docs
    logger.info(f"🔍 [execute_search] → {len(unique_docs)} documents uniques (stratégie: {strategy})")
    return state


def rerank_results(state: AgentState) -> AgentState:
    """Nœud 4: Applique le reranking cross-encoder."""
    docs = state.get("retrieved_docs", [])
    query = state["query"]

    if not docs:
        _add_thought(state, "rerank_results", "Aucun document à reranker")
        state["reranked_docs"] = []
        return state

    tools: RetrievalTools = state.get("_tools")  # type: ignore[assignment]
    if tools is None:
        state["reranked_docs"] = docs[:10]
        return state

    _add_thought(state, "rerank_results", f"Reranking de {len(docs)} documents")

    result = tools.rerank_documents(query, docs, top_k=min(10, len(docs)))
    _add_tool_call(state, "rerank", result.params, result.to_observation())

    state["reranked_docs"] = result.documents
    logger.info(f"📊 [rerank_results] → {len(result.documents)} documents rerankés")
    return state


def evaluate_quality(state: AgentState) -> AgentState:
    """Nœud 5: Évalue la qualité du contexte récupéré."""
    docs = state.get("reranked_docs", state.get("retrieved_docs", []))
    query = state["query"]

    if not docs:
        state["quality_score"] = 0.0
        state["quality_sufficient"] = False
        state["quality_feedback"] = "Aucun document récupéré"
        _add_thought(state, "evaluate_quality", "Score: 0.0 — Aucun document")
        return state

    # Construire le contexte pour l'évaluateur
    context_parts = []
    for i, doc in enumerate(docs[:8], 1):
        text = doc.get("text", "")[:300]
        score = doc.get("score", 0.0)
        context_parts.append(f"[Doc {i}] (score={score:.3f}) {text}")
    context_str = "\n\n".join(context_parts)

    prompt = QUALITY_EVALUATOR_PROMPT.format(query=query, context=context_str)
    parsed = _call_llm_json(prompt, temperature=0.1, max_tokens=512, max_retries=3)

    try:
        qs_val = parsed.get("quality_score", 0.5)
        quality_score = float(qs_val) if qs_val is not None else 0.5
    except (ValueError, TypeError):
        quality_score = 0.5
        
    is_sufficient = parsed.get("is_sufficient", quality_score >= QUALITY_THRESHOLD)
    if is_sufficient is None:
        is_sufficient = quality_score >= QUALITY_THRESHOLD
        
    feedback = parsed.get("feedback", "Évaluation non disponible")

    state["quality_score"] = quality_score
    state["quality_sufficient"] = is_sufficient
    state["quality_feedback"] = feedback

    _add_thought(state, "evaluate_quality",
                 f"Score: {quality_score:.2f} | Suffisant: {is_sufficient} | {feedback}")

    logger.info(f"✅ [evaluate_quality] score={quality_score:.2f} sufficient={is_sufficient}")
    return state


def handle_fallback(state: AgentState) -> AgentState:
    """Nœud 6: Gère le fallback quand la qualité est insuffisante."""
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", DEFAULT_MAX_ITERATIONS)
    tried = state.get("strategies_tried", [])
    query = state["query"]

    _add_thought(state, "handle_fallback",
                 f"Qualité insuffisante (itération {iteration}/{max_iter}). "
                 f"Stratégies essayées: {tried}")

    if iteration >= max_iter:
        _add_thought(state, "handle_fallback",
                     "Limite d'itérations atteinte — passage à la synthèse avec le contexte disponible")
        state["quality_sufficient"] = True  # Forcer la synthèse
        return state

    # Demander au LLM une stratégie de fallback
    prompt = FALLBACK_STRATEGY_PROMPT.format(
        query=query,
        previous_strategy=state.get("search_strategy", "dense"),
        quality_feedback=state.get("quality_feedback", ""),
        tried_strategies=", ".join(str(t) for t in tried if t),
    )
    parsed = _call_llm_json(prompt, temperature=0.2, max_tokens=256, max_retries=3)

    next_strategy = parsed.get("next_strategy", "dense")
    reasoning = parsed.get("reasoning", "")
    reformulated = parsed.get("reformulated_query")

    # Si la requête est reformulée, l'utiliser
    if reformulated and reformulated.strip():
        state["query"] = reformulated
        _add_thought(state, "handle_fallback",
                     f"Requête reformulée: '{reformulated[:80]}'")

    state["search_strategy"] = next_strategy
    _add_thought(state, "handle_fallback",
                 f"Nouvelle stratégie: {next_strategy} | {reasoning}")

    logger.info(f"🔄 [handle_fallback] → {next_strategy} (itération {iteration + 1})")
    return state


def synthesize_response(state: AgentState) -> AgentState:
    """Nœud 7: Synthétise la réponse finale à partir du contexte."""
    docs = state.get("reranked_docs", state.get("retrieved_docs", []))
    query = state["query"]

    _add_thought(state, "synthesize_response",
                 f"Synthèse avec {len(docs)} documents")

    # Construire les sources
    sources = []
    for doc in docs:
        meta = doc.get("metadata", {})
        sources.append({
            "filename": doc.get("filename") or meta.get("filename", "inconnu"),
            "score": round(float(doc.get("score", 0)), 4),
            "chunk_index": doc.get("chunk_index") or meta.get("chunk_index", 0),
            "excerpt": doc.get("text", ""),
        })

    state["sources"] = sources

    if not docs:
        state["final_response"] = (
            "Je n'ai pas trouvé d'information pertinente dans la base de connaissances "
            "pour répondre à cette question."
        )
        return state

    # Construire le contexte pour la synthèse
    from seinentai4us_api.utils.functions import format_context
    context_str = format_context(docs)

    # Ajouter le contexte conversationnel si disponible
    conv_context = state.get("conversation_context", "")
    if conv_context:
        full_prompt = (
            f"Contexte de la conversation précédente:\n{conv_context}\n\n"
            + SYNTHESIS_PROMPT.format(query=query, context=context_str)
        )
    else:
        full_prompt = SYNTHESIS_PROMPT.format(query=query, context=context_str)

    state["synthesis_prompt"] = full_prompt

    logger.info(f"📝 [synthesize_response] → Prompt généré pour streaming")
    return state


# ── Routing conditionnel ──────────────────────────────────────────────────────

def route_after_analysis(state: AgentState) -> str:
    """Détermine le prochain nœud après l'analyse."""
    if state.get("sub_queries"):
        return "decompose_query"
    return "execute_search"


def route_after_evaluation(state: AgentState) -> str:
    """Détermine le prochain nœud après l'évaluation de qualité."""
    if state.get("quality_sufficient", False):
        return "synthesize_response"
    return "handle_fallback"


def route_after_fallback(state: AgentState) -> str:
    """Détermine le prochain nœud après le fallback."""
    if state.get("quality_sufficient", False):
        return "synthesize_response"
    return "execute_search"


# ── Construction du graphe ────────────────────────────────────────────────────

def build_agent_graph(retrieval_tools: RetrievalTools) -> StateGraph:
    """
    Construit et compile le graphe LangGraph pour l'agent RAG.

    Args:
        retrieval_tools: Instance de RetrievalTools injectée.

    Returns:
        Graphe compilé prêt à être exécuté.
    """
    # Injecter les tools dans chaque nœud via un wrapper
    def _inject_tools(node_fn):
        """Wrapper qui injecte les outils dans le state avant chaque nœud."""
        def wrapped(state: AgentState) -> AgentState:
            state["_tools"] = retrieval_tools  # type: ignore[assignment]
            result = node_fn(state)
            # Retirer la référence pour ne pas polluer le state sérialisé
            result.pop("_tools", None)
            return result
        return wrapped

    graph = StateGraph(AgentState)

    # Ajouter les nœuds
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("decompose_query", decompose_query)
    graph.add_node("execute_search", _inject_tools(execute_search))
    graph.add_node("rerank_results", _inject_tools(rerank_results))
    graph.add_node("evaluate_quality", evaluate_quality)
    graph.add_node("handle_fallback", handle_fallback)
    graph.add_node("synthesize_response", synthesize_response)

    # Point d'entrée
    graph.set_entry_point("analyze_query")

    # Edges
    graph.add_conditional_edges("analyze_query", route_after_analysis, {
        "decompose_query": "decompose_query",
        "execute_search": "execute_search",
    })
    graph.add_edge("decompose_query", "execute_search")
    graph.add_edge("execute_search", "rerank_results")
    graph.add_edge("rerank_results", "evaluate_quality")
    graph.add_conditional_edges("evaluate_quality", route_after_evaluation, {
        "synthesize_response": "synthesize_response",
        "handle_fallback": "handle_fallback",
    })
    graph.add_conditional_edges("handle_fallback", route_after_fallback, {
        "execute_search": "execute_search",
        "synthesize_response": "synthesize_response",
    })
    graph.add_edge("synthesize_response", END)

    return graph.compile()
