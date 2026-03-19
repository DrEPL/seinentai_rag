"""
Service d'authentification — SEINENTAI4US
Gestion des utilisateurs et tokens API (in-memory + fichier JSON pour la persistance simple).
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.models.schemas import UserProfile

logger = logging.getLogger(__name__)

# Fichier de persistance simple (en prod: remplacer par PostgreSQL/Redis)
USERS_FILE = Path("data/users.json")
TOKENS_FILE = Path("data/tokens.json")


def _hash_password(password: str) -> str:
    """Hash SHA-256 avec le secret comme sel."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256,
    ).hexdigest()


def _load_json(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("{}")
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class AuthService:
    """Service d'authentification simple par token."""

    # ── Utilisateurs ──────────────────────────────────────────────────────────

    def register(self, email: str, password: str, full_name: str) -> Optional[UserProfile]:
        users = _load_json(USERS_FILE)

        if email in users:
            return None  # Déjà existant

        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        users[email] = {
            "id": user_id,
            "email": email,
            "password_hash": _hash_password(password),
            "full_name": full_name,
            "created_at": now,
            "is_active": True,
        }
        _save_json(USERS_FILE, users)
        logger.info(f"✅ Nouvel utilisateur enregistré : {email}")

        return UserProfile(
            id=user_id,
            email=email,
            full_name=full_name,
            created_at=datetime.fromisoformat(now),
        )

    def authenticate(self, email: str, password: str) -> Optional[UserProfile]:
        users = _load_json(USERS_FILE)
        user = users.get(email)
        if not user:
            return None
        if not user.get("is_active", True):
            return None
        if user["password_hash"] != _hash_password(password):
            return None

        return UserProfile(
            id=user["id"],
            email=email,
            full_name=user["full_name"],
            created_at=datetime.fromisoformat(user["created_at"]),
            is_active=user.get("is_active", True),
        )

    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        users = _load_json(USERS_FILE)
        for email, u in users.items():
            if u["id"] == user_id:
                return UserProfile(
                    id=u["id"],
                    email=email,
                    full_name=u["full_name"],
                    created_at=datetime.fromisoformat(u["created_at"]),
                    is_active=u.get("is_active", True),
                )
        return None

    # ── Tokens ────────────────────────────────────────────────────────────────

    def create_token(self, user_id: str) -> str:
        tokens = _load_json(TOKENS_FILE)
        token = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")
        expire = (datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)).isoformat()
        tokens[token] = {"user_id": user_id, "expires_at": expire}
        _save_json(TOKENS_FILE, tokens)
        logger.info(f"🔑 Token créé pour user_id={user_id}")
        return token

    def validate_token(self, token: str) -> Optional[str]:
        """Retourne user_id si le token est valide, None sinon."""
        tokens = _load_json(TOKENS_FILE)
        entry = tokens.get(token)
        if not entry:
            return None
        if datetime.utcnow() > datetime.fromisoformat(entry["expires_at"]):
            # Nettoyage du token expiré
            del tokens[token]
            _save_json(TOKENS_FILE, tokens)
            return None
        return entry["user_id"]

    def revoke_token(self, token: str) -> bool:
        tokens = _load_json(TOKENS_FILE)
        if token in tokens:
            del tokens[token]
            _save_json(TOKENS_FILE, tokens)
            logger.info("🚪 Token révoqué.")
            return True
        return False


auth_service = AuthService()
