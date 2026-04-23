"""
Router Authentification — SEINENTAI4US
POST /auth/register | POST /auth/login | POST /auth/logout | GET /auth/me
PATCH /auth/tutorial-state
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Optional

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.dependencies.auth import get_current_user
from seinentai4us_api.api.models.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UpdateTutorialStateRequest,
    UserProfile,
)
from seinentai4us_api.api.services.auth_service import auth_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte utilisateur",
)
async def register(body: RegisterRequest):
    """
    Crée un nouveau compte utilisateur.

    - **email** : adresse email unique
    - **password** : minimum 8 caractères
    - **full_name** : nom complet
    """
    user = await auth_service.register(body.email, body.password, body.full_name)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un compte avec l'email '{body.email}' existe déjà.",
        )
    logger.info(f"Nouvel utilisateur : {body.email}")
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion et obtention d'un token API",
)
async def login(body: LoginRequest):
    """
    Authentifie un utilisateur et retourne un token Bearer.

    Ce token doit être inclus dans toutes les requêtes suivantes sous la forme :
    `Authorization: Bearer <token>`

    Le champ `user.login_count` indique le numéro de connexion courant.
    Le champ `user.tutorial_state` permet au frontend de décider si le tutoriel doit s'afficher.
    """
    user = await auth_service.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    token = await auth_service.create_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=settings.TOKEN_EXPIRE_HOURS * 3600,
        user=user,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Déconnexion (révocation du token)",
)
async def logout(
    authorization: Optional[str] = Header(None),
    current_user: UserProfile = Depends(get_current_user),
):
    """Révoque le token courant."""
    if authorization:
        token = authorization.split()[-1]
        await auth_service.revoke_token(token)
    return MessageResponse(message="Déconnexion réussie.")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Profil de l'utilisateur connecté",
)
async def me(current_user: UserProfile = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur authentifié."""
    return current_user


@router.patch(
    "/tutorial-state",
    response_model=UserProfile,
    summary="Mettre à jour l'état du tutoriel d'onboarding",
)
async def update_tutorial_state(
    body: UpdateTutorialStateRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Met à jour l'état du tutoriel pour l'utilisateur connecté.

    - **seen** : l'utilisateur a vu le tutoriel mais peut le revoir (reporter)
    - **dismissed** : l'utilisateur ne souhaite plus voir le tutoriel automatiquement
    """
    updated_user = await auth_service.update_tutorial_state(current_user.id, body.state)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )
    logger.info(
        "Tutorial state mis à jour pour %s : %s → %s",
        current_user.email,
        current_user.tutorial_state,
        body.state,
    )
    return updated_user
