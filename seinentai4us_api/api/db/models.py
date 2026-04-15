from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class UserDocument(Document):
    user_id: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Settings:
        name = "users"


class AuthTokenDocument(Document):
    token: Indexed(str, unique=True)
    user_id: Indexed(str)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "auth_tokens"


class ConversationDocument(Document):
    conversation_id: Indexed(str, unique=True)
    user_id: Indexed(str)
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    archived: bool = False

    class Settings:
        name = "conversations"


class MessageDocument(Document):
    message_id: Indexed(str, unique=True)
    conversation_id: Indexed(str)
    user_id: Indexed(str)
    role: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "messages"


class IndexedDocument(Document):
    document_id: Indexed(str, unique=True)
    filename: Indexed(str)
    bucket: str
    object_key: str
    minio_etag: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    status: str = "uploaded"
    qdrant_doc_id: Optional[str] = None
    chunk_count: Optional[int] = None
    indexed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "indexed_documents"
