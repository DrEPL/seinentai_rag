"""
Service de gestion des sessions de chat — SEINENTAI4US
Persistance in-memory + fichier JSON.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

SESSIONS_FILE = Path("data/chat_sessions.json")


def _load() -> dict:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("{}")
    try:
        return json.loads(SESSIONS_FILE.read_text())
    except Exception:
        return {}


def _save(data: dict) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(data, indent=2, default=str))


class ChatSessionService:
    """Gestion des sessions de conversation."""

    def create_session(self, user_id: str) -> str:
        sessions = _load()
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        _save(sessions)
        logger.info(f"💬 Nouvelle session créée : {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        sessions = _load()
        return sessions.get(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        sessions = _load()
        if session_id not in sessions:
            raise ValueError(f"Session introuvable : {session_id}")

        msg = {
            "message_id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": sources or [],
            "metadata": metadata or {},
        }
        sessions[session_id]["messages"].append(msg)
        sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
        _save(sessions)
        return msg

    def get_history(self, session_id: str) -> List[Dict]:
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get("messages", [])

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        sessions = _load()
        result = []
        for sid, s in sessions.items():
            if s.get("user_id") == user_id:
                result.append({
                    "session_id": sid,
                    "created_at": s["created_at"],
                    "updated_at": s["updated_at"],
                    "message_count": len(s.get("messages", [])),
                })
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result

    def delete_session(self, session_id: str) -> bool:
        sessions = _load()
        if session_id in sessions:
            del sessions[session_id]
            _save(sessions)
            return True
        return False

    def build_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Construit le contexte de conversation pour le LLM."""
        history = self.get_history(session_id)
        recent = history[-max_messages:]
        lines = []
        for msg in recent:
            prefix = "Utilisateur" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)


chat_session_service = ChatSessionService()
