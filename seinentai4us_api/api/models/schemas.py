"""
Modèles Pydantic — SEINENTAI4US
Tous les schémas de requête / réponse sont définis ici.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 caractères")
    full_name: str = Field(..., min_length=2, max_length=100)

    model_config = {"json_schema_extra": {"example": {
        "email": "user@seinentai.jp",
        "password": "MonMotDePasse123",
        "full_name": "Tanaka Yuki"
    }}}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {"example": {
        "email": "user@seinentai.jp",
        "password": "MonMotDePasse123"
    }}}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # secondes
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool = True


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentStatus(BaseModel):
    filename: str
    status: str  # "indexed" | "pending" | "not_found" | "error"
    doc_id: Optional[str] = None
    chunk_count: Optional[int] = None
    indexed_at: Optional[datetime] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None


class DocumentListItem(BaseModel):
    filename: str
    size: Optional[int] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None
    content_type: Optional[str] = None
    indexed: bool = False
    chunk_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentListItem]


class ReindexRequest(BaseModel):
    force: bool = Field(False, description="Forcer la réindexation même si déjà indexé")
    filenames: Optional[List[str]] = Field(None, description="Liste de fichiers spécifiques (None = tous)")


class ReindexResponse(BaseModel):
    total: int
    success: int
    skipped: int
    failed: int
    details: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE
# ═══════════════════════════════════════════════════════════════════════════════

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(5, ge=1, le=50)
    score_threshold: float = Field(0.0, ge=0.0, le=1.0)
    filename_filter: Optional[str] = Field(None, description="Filtrer par nom de fichier")
    use_hybrid: bool = Field(False, description="Activer la recherche hybride (dense + sparse)")
    use_hyde: bool = Field(False, description="Active HyDE pour enrichir la requête dense")

    model_config = {"json_schema_extra": {"example": {
        "query": "Quelles sont les activités du groupe des jeunes ?",
        "limit": 5,
        "score_threshold": 0.2,
        "use_hybrid": True,
        "use_hyde": False,
    }}}


class SearchResult(BaseModel):
    text: str
    filename: str
    score: float
    chunk_index: int
    total_chunks: Optional[int] = None
    doc_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    search_time_ms: float


class HybridSearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    search_type: str = "hybrid"
    search_time_ms: float


class RerankResult(BaseModel):
    text: str
    filename: str
    original_score: float
    boosted_score: float
    chunk_index: int


class RerankResponse(BaseModel):
    query: str
    results: List[RerankResult]
    total: int
    boost_field: str
    boost_value: Any


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════════════════════════════════

class NewChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=64, le=8192)
    template: Optional[str] = Field(None, description="Nom du template de prompt")
    search_limit: int = Field(5, ge=1, le=20, description="Nombre de chunks à récupérer")
    score_threshold: float = Field(0.0, ge=0.0, le=1.0)
    stream: bool = Field(False, description="Activer le streaming SSE")
    use_hyde: bool = Field(False, description="Active HyDE pour enrichir la requête dense")
    use_hybrid: bool = Field(False, description="Activer la recherche hybride (dense + sparse)")
    use_agent: bool = Field(True, description="Utiliser l'agent RAG intelligent (LangGraph)")

    model_config = {"json_schema_extra": {"example": {
        "message": "Quelles sont les valeurs du groupe des jeunes ?",
        "temperature": 0.7,
        "stream": False,
        "use_agent": True
    }}}


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatSession(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: List[ChatMessage] = []


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    sources: List[Dict[str, Any]]
    model: str
    generation_time: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    timestamp: datetime
    agent_trace: Optional[Dict[str, Any]] = Field(None, description="Trace de raisonnement de l'agent")


class ChatHistoryRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    stream: bool = False
    use_hyde: bool = Field(False, description="Active HyDE pour enrichir la requête dense")
    use_hybrid: bool = Field(False, description="Activer la recherche hybride (dense + sparse)")
    use_agent: bool = Field(True, description="Utiliser l'agent RAG intelligent (LangGraph)")


class SessionListResponse(BaseModel):
    total: int
    sessions: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN / SANTÉ
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceHealth(BaseModel):
    name: str
    status: str  # "ok" | "error" | "degraded"
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    timestamp: datetime
    version: str = "1.0.0"
    services: List[ServiceHealth]
    uptime_seconds: Optional[float] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None
