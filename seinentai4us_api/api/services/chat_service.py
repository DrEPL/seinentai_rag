"""Service de gestion conversationnelle avec persistance MongoDB."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.db.models import ConversationDocument, MessageDocument

logger = logging.getLogger(__name__)


class ChatSessionService:
    async def create_session(self, user_id: str, title: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        conversation = ConversationDocument(
            conversation_id=session_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )
        await conversation.insert()
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        conv = await ConversationDocument.find_one(
            ConversationDocument.conversation_id == session_id
        )
        if not conv:
            return None
        messages = await MessageDocument.find(
            MessageDocument.conversation_id == session_id
        ).sort(MessageDocument.created_at).to_list()

        return {
            "session_id": conv.conversation_id,
            "user_id": conv.user_id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "messages": [
                {
                    "message_id": m.message_id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.created_at,
                    "sources": m.sources,
                    "metadata": m.metadata,
                }
                for m in messages
            ],
        }

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        conv = await ConversationDocument.find_one(
            ConversationDocument.conversation_id == session_id
        )
        if not conv:
            raise ValueError(f"Session introuvable : {session_id}")

        now = datetime.utcnow()
        msg = MessageDocument(
            message_id=str(uuid.uuid4()),
            conversation_id=session_id,
            user_id=conv.user_id,
            role=role,
            content=content,
            sources=sources or [],
            metadata=metadata or {},
            created_at=now,
        )
        await msg.insert()

        conv.updated_at = now
        conv.last_message_at = now
        if not conv.title and role == "user":
            conv.title = content[:80]
        await conv.save()

        return {
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at,
            "sources": msg.sources,
            "metadata": msg.metadata,
        }

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        messages = await MessageDocument.find(
            MessageDocument.conversation_id == session_id
        ).sort(MessageDocument.created_at).to_list()
        return [
            {
                "message_id": m.message_id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at,
                "sources": m.sources,
                "metadata": m.metadata,
            }
            for m in messages
        ]

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        sessions = await ConversationDocument.find(
            ConversationDocument.user_id == user_id
        ).sort(-ConversationDocument.updated_at).to_list()

        results: List[Dict[str, Any]] = []
        for conv in sessions:
            message_count = await MessageDocument.find(
                MessageDocument.conversation_id == conv.conversation_id
            ).count()
            results.append(
                {
                    "session_id": conv.conversation_id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": message_count,
                }
            )
        return results

    async def delete_session(self, session_id: str) -> bool:
        conv = await ConversationDocument.find_one(
            ConversationDocument.conversation_id == session_id
        )
        if not conv:
            return False

        await MessageDocument.find(
            MessageDocument.conversation_id == session_id
        ).delete()
        await conv.delete()
        return True

    async def build_conversation_context(
        self,
        session_id: str,
        max_messages: Optional[int] = None,
        max_chars: Optional[int] = None,
    ) -> str:
        max_messages = max_messages or settings.CONTEXT_MAX_MESSAGES
        max_chars = max_chars or settings.CONTEXT_MAX_CHARS

        history = await self.get_history(session_id)
        recent = history[-max_messages:]
        lines: List[str] = []
        current_size = 0

        for msg in reversed(recent):
            prefix = "Utilisateur" if msg["role"] == "user" else "Assistant"
            row = f"{prefix}: {msg['content']}"
            projected = current_size + len(row) + 1
            if projected > max_chars:
                break
            lines.append(row)
            current_size = projected

        return "\n".join(reversed(lines))


chat_session_service = ChatSessionService()
