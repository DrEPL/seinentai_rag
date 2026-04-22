"""
Router Chat — SEINENTAI4US
POST /chat/new          - Nouveau chat (réponse directe ou SSE)
POST /chat/{session_id} - Continuer un chat (SSE)
GET  /chat/history      - Liste des sessions de l'utilisateur
GET  /chat/sessions/{session_id} - Historique d'une session

Supporte trois modes (routage intelligent) :
- mode "direct"  → Réponse LLM directe (small talk, hors domaine, clarification)
- mode "agent"   → Agent RAG intelligent (LangGraph) avec raisonnement dynamique
- mode "static"  → Pipeline RAG statique (compatibilité descendante)
"""

import json
import logging
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from seinentai4us_api.api.dependencies.auth import get_current_user
from seinentai4us_api.api.models.schemas import (
    ChatHistoryRequest,
    ChatResponse,
    ChatSession,
    NewChatRequest,
    SessionListResponse,
    UserProfile,
)
from seinentai4us_api.api.services.chat_service import chat_session_service
from seinentai4us_api.api.services.rag_service import rag_service
from seinentai4us_api.api.services.intent_router import get_intent_router

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_sources(docs: list) -> list:
    sources = []
    for i, d in enumerate(docs):
        meta = d.get("metadata", {})
        text = d.get("text", "")
        sources.append({
            "id": str(i),
            "filename": d.get("filename") or meta.get("filename", "inconnu"),
            "title": meta.get("title") or d.get("filename") or meta.get("filename") or f"Document {i+1}",
            "score": round(float(d.get("score", 0)), 4),
            "chunk_index": d.get("chunk_index") or meta.get("chunk_index", 0),
            "content": text,
            "excerpt": text,
            "url": meta.get("url"),
        })
    return sources


def _get_agentic_service():
    """Récupère le service agentique (lazy import pour éviter les imports circulaires)."""
    from seinentai4us_api.api.services.agentic_rag_service import get_agentic_service
    return get_agentic_service()

# ─── SSE Stream (Réponse directe — sans RAG) ─────────────────────────────────

async def _sse_stream_direct(
    session_id: str,
    message: str,
    intent_result,
) -> AsyncGenerator[str, None]:
    """
    Générateur SSE pour les réponses directes (small_talk, out_of_domain, ambiguous).
    Ne déclenche pas le pipeline RAG.
    """
    from Agent.prompts import DIRECT_RESPONSE_SYSTEM_PROMPT

    # Événement initial
    init_event = {
        "type": "start",
        "session_id": session_id,
        "mode": "direct",
        "intent": intent_result.intent,
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

    # Thought : classification d'intention
    yield f"data: {json.dumps({'type': 'thought', 'node': 'intent_router', 'content': f'Intent: {intent_result.intent} (confiance: {intent_result.confidence:.0%}) — {intent_result.reasoning}', 'timestamp': datetime.utcnow().isoformat()}, ensure_ascii=False)}\n\n"

    # Synthèse start
    yield f"data: {json.dumps({'type': 'synthesis_start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

    full_response = []

    # Si le classificateur a déjà fourni une réponse directe, la streamer
    if intent_result.direct_response:
        response_text = intent_result.direct_response
        # Simuler un streaming token par token (mots)
        words = response_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else f" {word}"
            full_response.append(token)
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
    elif intent_result.follow_up_question:
        # Ambiguous : streamer la question de clarification
        response_text = intent_result.follow_up_question
        words = response_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else f" {word}"
            full_response.append(token)
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
    else:
        # Fallback : générer via LLM en streaming
        intent_router = get_intent_router()
        prompt = f"L'utilisateur dit : \"{message}\"\nRéponds de manière naturelle et chaleureuse."
        for token in intent_router._call_llm_stream(
            prompt, system=DIRECT_RESPONSE_SYSTEM_PROMPT, temperature=0.7, max_tokens=512
        ):
            if token:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

    # Sauvegarder dans l'historique
    response_text = "".join(full_response)
    await chat_session_service.add_message(session_id, "user", message)
    await chat_session_service.add_message(
        session_id, "assistant", response_text,
        metadata={"intent": intent_result.intent, "mode": "direct"},
    )

    # Événement final
    end_event = {
        "type": "done",
        "session_id": session_id,
        "message_id": str(uuid.uuid4()),
        "sources": [],
        "intent": intent_result.intent,
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(end_event, ensure_ascii=False)}\n\n"


# ─── SSE Stream (Pipeline statique) ──────────────────────────────────────────


async def _sse_stream_static(
    session_id: str,
    message: str,
    generation_query: str,
    docs: list,
    **gen_kwargs,
) -> AsyncGenerator[str, None]:
    """Générateur SSE pour le pipeline statique (compatibilité descendante)."""
    sources = _build_sources(docs)
    full_response = []

    # Événement initial (métadonnées)
    init_event = {
        "type": "start",
        "session_id": session_id,
        "mode": "static",
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

    # 1. Thought
    yield f"data: {json.dumps({'type': 'thought', 'content': 'Recherche de documents pertinents...', 'timestamp': datetime.utcnow().isoformat()}, ensure_ascii=False)}\n\n"
    
    # 2. Observation (Analyse)
    best_score = docs[0].get("score", 0) if docs else 0
    yield f"data: {json.dumps({'type': 'observation', 'content': f'{len(docs)} documents trouvés', 'score': float(best_score), 'timestamp': datetime.utcnow().isoformat()}, ensure_ascii=False)}\n\n"

    # 3. Synthesis Start
    yield f"data: {json.dumps({'type': 'synthesis_start', 'timestamp': datetime.utcnow().isoformat()}, ensure_ascii=False)}\n\n"

    try:
        for token, done in rag_service.generate_stream(generation_query, docs, **gen_kwargs):
            full_response.append(token)
            chunk_event = {"type": "token", "token": token}
            yield f"data: {json.dumps(chunk_event)}\n\n"
            if done:
                break
    except Exception as e:
        error_event = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_event)}\n\n"
        return

    # Sauvegarder dans l'historique
    response_text = "".join(full_response)
    await chat_session_service.add_message(session_id, "user", message)
    await chat_session_service.add_message(session_id, "assistant", response_text, sources=sources)

    # Événement final
    end_event = {
        "type": "done",
        "session_id": session_id,
        "message_id": str(uuid.uuid4()),
        "sources": sources,
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(end_event, ensure_ascii=False)}\n\n"


# ─── SSE Stream (Agent RAG intelligent) ──────────────────────────────────────

async def _sse_stream_agent(
    session_id: str,
    message: str,
    conversation_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Générateur SSE pour l'agent LangGraph.

    Émet les événements suivants :
    - {"type": "start", "mode": "agent", ...}
    - {"type": "thought", "node": "...", "content": "..."}
    - {"type": "tool_call", "tool": "...", "params": {...}, "result": "..."}
    - {"type": "observation", "content": "..."}
    - {"type": "synthesis_start"}
    - {"type": "token", "token": "..."} (réponse finale en un seul bloc)
    - {"type": "done", "sources": [...], "agent_trace": {...}}
    - {"type": "error", "message": "..."}
    """
    agent_service = _get_agentic_service()

    # Événement initial
    init_event = {
        "type": "start",
        "session_id": session_id,
        "mode": "agent",
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

    full_response = ""
    sources = []
    agent_trace = {}

    try:
        for event in agent_service.stream(
            query=message,
            conversation_context=conversation_context,
        ):
            event_type = event.get("type", "")

            if event_type == "thought":
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif event_type == "tool_call":
                # Simplifier les params pour le streaming (éviter les gros payloads)
                simplified = {
                    "type": "tool_call",
                    "tool": event.get("tool", ""),
                    "params": {
                        k: v for k, v in event.get("params", {}).items()
                        if k != "query" or len(str(v)) < 200
                    },
                    "result_preview": event.get("result", "")[:300],
                    "timestamp": event.get("timestamp", ""),
                }
                yield f"data: {json.dumps(simplified, ensure_ascii=False)}\n\n"

            elif event_type == "observation":
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            elif event_type == "synthesis_start":
                yield f"data: {json.dumps({'type': 'synthesis_start'})}\n\n"

            elif event_type == "token":
                token_content = event.get("content", "")
                full_response += token_content
                yield f"data: {json.dumps({'type': 'token', 'token': token_content})}\n\n"

            elif event_type == "response":
                # Fallback pour le mode non-stream si jamais on reçoit la réponse en un bloc
                if not full_response:
                    full_response = event.get("content", "")
                    yield f"data: {json.dumps({'type': 'token', 'token': full_response})}\n\n"

            elif event_type == "done":
                sources = event.get("sources", [])
                agent_trace = event.get("agent_trace", {})

            elif event_type == "error":
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                return

    except Exception as e:
        logger.error(f"Agent stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return

    # Sauvegarder dans l'historique
    await chat_session_service.add_message(session_id, "user", message)
    await chat_session_service.add_message(
        session_id, "assistant", full_response, sources=sources
    )

    # Événement final
    end_event = {
        "type": "done",
        "session_id": session_id,
        "message_id": str(uuid.uuid4()),
        "sources": sources,
        "agent_trace": agent_trace,
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(end_event, ensure_ascii=False)}\n\n"


# ─── Nouveau chat ─────────────────────────────────────────────────────────────

@router.post(
    "/new",
    summary="Démarrer un nouveau chat RAG",
    responses={
        200: {"description": "Réponse directe (stream=false) ou SSE (stream=true)"},
    },
)
async def new_chat(
    body: NewChatRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Crée une nouvelle session de chat et génère une réponse RAG.

    - Si `use_agent=true` : utilise l'agent LangGraph intelligent
    - Si `use_agent=false` : utilise le pipeline RAG statique
    - Si `stream=true` : retourne un flux `text/event-stream` (SSE)
    - Si `stream=false` : retourne un objet JSON `ChatResponse`

    Événements SSE (mode agent) :
    - `type`: `"start"` | `"thought"` | `"tool_call"` | `"observation"` |
              `"synthesis_start"` | `"token"` | `"done"` | `"error"`
    """
    # 1. Créer la session
    session_id = await chat_session_service.create_session(
        current_user.id, title=body.message[:80]
    )

    # ── Classification d'intention (Intent Router) ────────────────────────
    try:
        intent_router = get_intent_router()
        intent_result = intent_router.classify(
            message=body.message,
            conversation_context="",  # Pas de contexte pour un nouveau chat
        )
        logger.info(
            f"🧠 [new_chat] Intent: {intent_result.intent} "
            f"(confidence={intent_result.confidence:.2f}, "
            f"time={intent_result.classification_time*1000:.0f}ms)"
        )
    except Exception as e:
        logger.warning(f"🧠 Intent classification failed, fallback to RAG: {e}")
        intent_result = None

    # ── Mode Direct (small_talk / out_of_domain / ambiguous) ──────────────
    if intent_result and intent_result.is_direct:
        if body.stream:
            return StreamingResponse(
                _sse_stream_direct(session_id, body.message, intent_result),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": session_id,
                    "X-RAG-Mode": "direct",
                },
            )

        # Réponse directe (non-streaming)
        response_text = intent_result.direct_response or intent_result.follow_up_question or ""
        if not response_text:
            # Fallback : générer via LLM
            from Agent.prompts import DIRECT_RESPONSE_SYSTEM_PROMPT
            prompt = f"L'utilisateur dit : \"{body.message}\"\nRéponds de manière naturelle et chaleureuse."
            tokens = list(intent_router._call_llm_stream(prompt, system=DIRECT_RESPONSE_SYSTEM_PROMPT, max_tokens=512))
            response_text = "".join(tokens)

        await chat_session_service.add_message(session_id, "user", body.message)
        await chat_session_service.add_message(
            session_id, "assistant", response_text,
            metadata={"intent": intent_result.intent, "mode": "direct"},
        )

        return ChatResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response=response_text,
            sources=[],
            model="direct-response",
            generation_time=intent_result.classification_time,
            timestamp=datetime.utcnow(),
        )

    # ── Mode Agent ────────────────────────────────────────────────────────
    if body.use_agent:
        if body.stream:
            return StreamingResponse(
                _sse_stream_agent(session_id, body.message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": session_id,
                    "X-RAG-Mode": "agent",
                },
            )

        # Réponse directe (agent)
        agent_service = _get_agentic_service()
        result = agent_service.run(query=body.message)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur agent: {result.get('error', 'Agent indisponible')}",
            )

        sources = result.get("sources", [])
        await chat_session_service.add_message(session_id, "user", body.message)
        await chat_session_service.add_message(
            session_id, "assistant", result["response"], sources=sources
        )

        return ChatResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response=result["response"],
            sources=sources,
            model=result.get("model", "agent-langgraph"),
            generation_time=result.get("generation_time", 0.0),
            timestamp=datetime.utcnow(),
            agent_trace=result.get("agent_trace"),
        )

    # ── Mode Statique (compatibilité descendante) ─────────────────────────
    docs = rag_service.search(
        query=body.message,
        limit=body.search_limit,
        score_threshold=body.score_threshold,
        use_hybrid=body.use_hybrid,
        use_hyde=body.use_hyde,
    )

    gen_kwargs = dict(
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        template=body.template,
    )

    if body.stream:
        return StreamingResponse(
            _sse_stream_static(
                session_id,
                body.message,
                body.message,
                docs,
                **gen_kwargs,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-ID": session_id,
                "X-RAG-Mode": "static",
            },
        )

    # Réponse directe (statique)
    await chat_session_service.add_message(session_id, "user", body.message)

    result = rag_service.generate(query=body.message, retrieved_docs=docs, **gen_kwargs)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur de génération : {result.get('error', 'Ollama indisponible')}",
        )

    sources = _build_sources(docs)
    await chat_session_service.add_message(
        session_id, "assistant", result["response"], sources=sources
    )

    return ChatResponse(
        session_id=session_id,
        message_id=str(uuid.uuid4()),
        response=result["response"],
        sources=sources,
        model=result.get("model", "unknown"),
        generation_time=result.get("generation_time", 0.0),
        prompt_tokens=result.get("prompt_tokens", 0),
        completion_tokens=result.get("completion_tokens", 0),
        timestamp=datetime.utcnow(),
    )


# ─── Continuer un chat ────────────────────────────────────────────────────────

@router.post(
    "/{session_id}",
    summary="Continuer un chat existant (SSE)",
    responses={
        200: {"description": "Flux SSE (text/event-stream) ou réponse directe"},
    },
)
async def continue_chat(
    session_id: str,
    body: ChatHistoryRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Envoie un message dans une session existante.

    - Prend en compte l'historique de la conversation pour contextualiser
    - Supporte les modes agent et statique
    """
    session = await chat_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' introuvable.",
        )
    if session.get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")

    # Enrichir la requête avec le contexte conversationnel
    conv_context = await chat_session_service.build_conversation_context(
        session_id, max_messages=6
    )

    # ── Classification d'intention (Intent Router) ────────────────────────
    try:
        intent_router = get_intent_router()
        intent_result = intent_router.classify(
            message=body.message,
            conversation_context=conv_context or "",
        )
        logger.info(
            f"🧠 [continue_chat] Intent: {intent_result.intent} "
            f"(confidence={intent_result.confidence:.2f}, "
            f"time={intent_result.classification_time*1000:.0f}ms)"
        )
    except Exception as e:
        logger.warning(f"🧠 Intent classification failed, fallback to RAG: {e}")
        intent_result = None

    # ── Mode Direct (small_talk / out_of_domain / ambiguous) ──────────────
    if intent_result and intent_result.is_direct:
        if body.stream:
            return StreamingResponse(
                _sse_stream_direct(session_id, body.message, intent_result),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": session_id,
                    "X-RAG-Mode": "direct",
                },
            )

        # Réponse directe (non-streaming)
        response_text = intent_result.direct_response or intent_result.follow_up_question or ""
        if not response_text:
            from Agent.prompts import DIRECT_RESPONSE_SYSTEM_PROMPT
            prompt = f"L'utilisateur dit : \"{body.message}\"\nRéponds de manière naturelle et chaleureuse."
            tokens = list(intent_router._call_llm_stream(prompt, system=DIRECT_RESPONSE_SYSTEM_PROMPT, max_tokens=512))
            response_text = "".join(tokens)

        await chat_session_service.add_message(session_id, "user", body.message)
        await chat_session_service.add_message(
            session_id, "assistant", response_text,
            metadata={"intent": intent_result.intent, "mode": "direct"},
        )

        return ChatResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response=response_text,
            sources=[],
            model="direct-response",
            generation_time=intent_result.classification_time,
            timestamp=datetime.utcnow(),
        )

    # ── Mode Agent ────────────────────────────────────────────────────────
    if body.use_agent:
        if body.stream:
            return StreamingResponse(
                _sse_stream_agent(
                    session_id,
                    body.message,
                    conversation_context=conv_context or "",
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Session-ID": session_id,
                    "X-RAG-Mode": "agent",
                },
            )

        # Réponse directe (agent)
        agent_service = _get_agentic_service()
        result = agent_service.run(
            query=body.message,
            conversation_context=conv_context or "",
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur agent: {result.get('error', 'Agent indisponible')}",
            )

        sources = result.get("sources", [])
        await chat_session_service.add_message(session_id, "user", body.message)
        await chat_session_service.add_message(
            session_id, "assistant", result["response"], sources=sources
        )

        return ChatResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response=result["response"],
            sources=sources,
            model=result.get("model", "agent-langgraph"),
            generation_time=result.get("generation_time", 0.0),
            timestamp=datetime.utcnow(),
            agent_trace=result.get("agent_trace"),
        )

    # ── Mode Statique ─────────────────────────────────────────────────────
    enriched_query = f"{conv_context}\n\nNouvelle question : {body.message}" if conv_context else body.message

    docs = rag_service.search(
        query=body.message,
        limit=10,
        score_threshold=0.4,
        use_hybrid=body.use_hybrid,
        use_hyde=body.use_hyde,
    )

    gen_kwargs = dict(temperature=body.temperature)
    
    if body.stream:
        return StreamingResponse(
            _sse_stream_static(
                session_id,
                body.message,
                enriched_query,
                docs,
                **gen_kwargs,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-ID": session_id,
                "X-RAG-Mode": "static",
            },
        )

    # Réponse directe (statique)
    await chat_session_service.add_message(session_id, "user", body.message)

    result = rag_service.generate(query=enriched_query, retrieved_docs=docs, **gen_kwargs)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur de génération : {result.get('error', 'Ollama indisponible')}",
        )

    sources = _build_sources(docs)
    await chat_session_service.add_message(
        session_id, "assistant", result["response"], sources=sources
    )

    return ChatResponse(
        session_id=session_id,
        message_id=str(uuid.uuid4()),
        response=result["response"],
        sources=sources,
        model=result.get("model", "unknown"),
        generation_time=result.get("generation_time", 0.0),
        prompt_tokens=result.get("prompt_tokens", 0),
        completion_tokens=result.get("completion_tokens", 0),
        timestamp=datetime.utcnow(),
    )


# ─── Historique ───────────────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=SessionListResponse,
    summary="Liste de toutes les sessions de l'utilisateur",
)
async def chat_history(current_user: UserProfile = Depends(get_current_user)):
    """Retourne la liste des sessions de chat de l'utilisateur connecté."""
    sessions = await chat_session_service.get_user_sessions(current_user.id)
    return SessionListResponse(total=len(sessions), sessions=sessions)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSession,
    summary="Détail d'une session (historique complet)",
)
async def get_session(
    session_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Retourne l'intégralité de l'historique d'une session de chat."""
    session = await chat_session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    from seinentai4us_api.api.models.schemas import ChatMessage
    messages = [
        ChatMessage(
            role=m["role"],
            content=m["content"],
            timestamp=m["timestamp"],
            sources=m.get("sources"),
            metadata=m.get("metadata"),
        )
        for m in session.get("messages", [])
    ]

    return ChatSession(
        session_id=session_id,
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=len(messages),
        messages=messages,
    )


@router.delete(
    "/sessions/{session_id}",
    summary="Supprime une session (soft delete)",
)
async def delete_session(
    session_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Marque une session comme supprimée (soft delete)."""
    # Vérifier l'existence et l'appartenance
    session = await chat_session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    success = await chat_session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Échec de la suppression.")

    return {"status": "success", "message": "Session supprimée avec succès."}
