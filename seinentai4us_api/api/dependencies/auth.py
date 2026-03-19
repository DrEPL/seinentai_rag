"""
Dépendances injectables FastAPI — SEINENTAI4US
"""

import logging
from fastapi import Depends, Header, HTTPException, status
from typing import Optional

from seinentai4us_api.api.models.schemas import UserProfile
from seinentai4us_api.api.services.auth_service import auth_service

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer <token>")
) -> UserProfile:
    """
    Extrait et valide le token Bearer de l'en-tête Authorization.
    Utilisé comme dépendance pour protéger les routes.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="En-tête Authorization manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format invalide. Utilisez : Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    user_id = auth_service.validate_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou désactivé.",
        )

    return user


def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[UserProfile]:
    """Retourne l'utilisateur si authentifié, None sinon (routes publiques)."""
    if not authorization:
        return None
    try:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            user_id = auth_service.validate_token(parts[1])
            if user_id:
                return auth_service.get_user_by_id(user_id)
    except Exception:
        pass
    return None
