"""Service d'authentification avec persistance MongoDB."""

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.db.models import AuthTokenDocument, UserDocument
from seinentai4us_api.api.models.schemas import UserProfile

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256,
    ).hexdigest()


def _to_user_profile(user: UserDocument) -> UserProfile:
    return UserProfile(
        id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        is_active=user.is_active,
        login_count=user.login_count,
        tutorial_state=user.tutorial_state,
        last_login_at=user.last_login_at,
    )


class AuthService:
    async def register(self, email: str, password: str, full_name: str) -> Optional[UserProfile]:
        existing_user = await UserDocument.find_one(UserDocument.email == email)
        if existing_user:
            return None

        user = UserDocument(
            user_id=str(uuid.uuid4()),
            email=email,
            password_hash=_hash_password(password),
            full_name=full_name,
            created_at=datetime.utcnow(),
            is_active=True,
            login_count=0,
            tutorial_state="never_seen",
            last_login_at=None,
        )
        await user.insert()
        logger.info("Nouvel utilisateur enregistre: %s", email)
        return _to_user_profile(user)

    async def authenticate(self, email: str, password: str) -> Optional[UserProfile]:
        user = await UserDocument.find_one(UserDocument.email == email)
        if not user or not user.is_active:
            return None
        if user.password_hash != _hash_password(password):
            return None

        # ─── Incrémenter le compteur de connexions ──────────────────────────
        user.login_count = (user.login_count or 0) + 1
        user.last_login_at = datetime.utcnow()
        await user.save()
        logger.info(
            "Connexion #%d pour user_id=%s (tutorial_state=%s)",
            user.login_count,
            user.user_id,
            user.tutorial_state,
        )
        return _to_user_profile(user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        user = await UserDocument.find_one(UserDocument.user_id == user_id)
        if not user:
            return None
        return _to_user_profile(user)

    async def create_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(48)
        token_doc = AuthTokenDocument(
            token=token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRE_HOURS),
        )
        await token_doc.insert()
        logger.info("Token cree pour user_id=%s", user_id)
        return token

    async def validate_token(self, token: str) -> Optional[str]:
        token_doc = await AuthTokenDocument.find_one(AuthTokenDocument.token == token)
        if not token_doc:
            return None
        if datetime.utcnow() > token_doc.expires_at:
            await token_doc.delete()
            return None
        return token_doc.user_id

    async def revoke_token(self, token: str) -> bool:
        token_doc = await AuthTokenDocument.find_one(AuthTokenDocument.token == token)
        if not token_doc:
            return False
        await token_doc.delete()
        return True

    async def update_tutorial_state(
        self,
        user_id: str,
        state: Literal["seen", "dismissed"],
    ) -> Optional[UserProfile]:
        """Met à jour l'état du tutoriel pour un utilisateur donné."""
        user = await UserDocument.find_one(UserDocument.user_id == user_id)
        if not user:
            return None
        user.tutorial_state = state
        await user.save()
        logger.info(
            "Tutorial state mis à jour: user_id=%s → %s",
            user_id,
            state,
        )
        return _to_user_profile(user)


auth_service = AuthService()
