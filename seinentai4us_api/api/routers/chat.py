"""
Router Chat — SEINENTAI4US
POST /chat/new          - Nouveau chat (réponse directe ou SSE)
POST /chat/{session_id} - Continuer un chat (SSE)
GET  /chat/history      - Liste des sessions de l'utilisateur
GET  /chat/sessions/{session_id} - Historique d'une session
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

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_sources(docs: list) -> list:
    sources = []
    for d in docs:
        meta = d.get("metadata", {})
        sources.append({
            "filename": d.get("filename") or meta.get("filename", "inconnu"),
            "score": round(float(d.get("score", 0)), 4),
            "chunk_index": d.get("chunk_index") or meta.get("chunk_index", 0),
            "excerpt": d.get("text", "") if d.get("text") else "",
            # "excerpt": (d.get("text", "")[:200] + "…") if d.get("text") else "",
        })
    return sources


async def _sse_stream(
    session_id: str,
    message: str,
    user_id: str,
    docs: list,
    **gen_kwargs,
) -> AsyncGenerator[str, None]:
    """Générateur SSE : envoie des événements data: token\\n\\n."""
    sources = _build_sources(docs)
    full_response = []

    # Événement initial (métadonnées)
    init_event = {
        "type": "start",
        "session_id": session_id,
        "sources": sources,
        "timestamp": datetime.utcnow().isoformat(),
    }
    yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"

    try:
        for token, done in rag_service.generate_stream(message, docs, **gen_kwargs):
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
    chat_session_service.add_message(session_id, "user", message)
    chat_session_service.add_message(session_id, "assistant", response_text, sources=sources)

    # Événement final
    end_event = {
        "type": "done",
        "session_id": session_id,
        "message_id": str(uuid.uuid4()),
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

    - Si `stream=false` : retourne un objet JSON `ChatResponse`
    - Si `stream=true`  : retourne un flux `text/event-stream` (SSE)

    Chaque événement SSE est un JSON avec les champs :
    - `type`: `"start"` | `"token"` | `"done"` | `"error"`
    - `token`: le token généré (type=token uniquement)
    - `sources`: liste des sources utilisées (type=start)
    """
    # 1. Créer la session
    session_id = chat_session_service.create_session(current_user.id)

    # 2. Récupérer les documents pertinents
    docs = rag_service.search(
        query=body.message,
        limit=body.search_limit,
        score_threshold=body.score_threshold,
        use_hybrid=True,
    )

    gen_kwargs = dict(
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        template=body.template,
    )

    # 3. Streaming SSE
    if body.stream:
        return StreamingResponse(
            _sse_stream(session_id, body.message, current_user.id, docs, **gen_kwargs),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-ID": session_id,
            },
        )

    # 4. Réponse directe
    chat_session_service.add_message(session_id, "user", body.message)

    result = rag_service.generate(query=body.message, retrieved_docs=docs, **gen_kwargs)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur de génération : {result.get('error', 'Ollama indisponible')}",
        )

    sources = _build_sources(docs)
    chat_session_service.add_message(session_id, "assistant", result["response"], sources=sources)

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
        200: {"description": "Flux SSE (text/event-stream)"},
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
    - Retourne toujours un flux SSE
    """
    session = chat_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' introuvable.",
        )
    if session.get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")

    # Enrichir la requête avec le contexte conversationnel
    conv_context = chat_session_service.build_conversation_context(session_id, max_messages=6)
    enriched_query = f"{conv_context}\n\nNouvelle question : {body.message}" if conv_context else body.message

    docs = rag_service.search(query=body.message, limit=10, score_threshold=0.4)

    gen_kwargs = dict(temperature=body.temperature)
    
    # 3. Streaming SSE
    if body.stream:
        return StreamingResponse(
            _sse_stream(session_id, body.message, current_user.id, docs, **gen_kwargs),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-ID": session_id,
            },
        )

    # 4. Réponse directe
    chat_session_service.add_message(session_id, "user", body.message)

    result = rag_service.generate(query=enriched_query, retrieved_docs=docs, **gen_kwargs)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur de génération : {result.get('error', 'Ollama indisponible')}",
        )

    sources = _build_sources(docs)
    chat_session_service.add_message(session_id, "assistant", result["response"], sources=sources)

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
    sessions = chat_session_service.get_user_sessions(current_user.id)
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
    session = chat_session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    from seinentai4us_api.api.models.schemas import ChatMessage
    messages = [
        ChatMessage(
            role=m["role"],
            content=m["content"],
            timestamp=datetime.fromisoformat(m["timestamp"]),
            sources=m.get("sources"),
            metadata=m.get("metadata"),
        )
        for m in session.get("messages", [])
    ]

    return ChatSession(
        session_id=session_id,
        created_at=datetime.fromisoformat(session["created_at"]),
        updated_at=datetime.fromisoformat(session["updated_at"]),
        message_count=len(messages),
        messages=messages,
    )
