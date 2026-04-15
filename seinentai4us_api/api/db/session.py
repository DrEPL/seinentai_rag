from __future__ import annotations

import logging
from typing import Optional

from beanie import init_beanie
from pymongo import AsyncMongoClient

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.db.models import (
    AuthTokenDocument,
    ConversationDocument,
    IndexedDocument,
    MessageDocument,
    UserDocument,
)

logger = logging.getLogger(__name__)

_mongo_client: Optional[AsyncMongoClient] = None


async def init_db() -> None:
    """Initialise la connexion MongoDB et les collections Beanie.

    Beanie 2.x s'appuie sur le client **asynchrone PyMongo** (`AsyncMongoClient`),
    pas sur Motor.
    """
    global _mongo_client

    if _mongo_client is not None:
        return

    _mongo_client = AsyncMongoClient(settings.mongodb_connection_string())
    db = _mongo_client[settings.MONGODB_DB_NAME]

    await init_beanie(
        database=db,
        document_models=[
            UserDocument,
            AuthTokenDocument,
            ConversationDocument,
            MessageDocument,
            IndexedDocument,
        ],
    )
    logger.info("MongoDB initialise avec Beanie.")


async def close_db() -> None:
    """Ferme proprement le client MongoDB."""
    global _mongo_client
    if _mongo_client is not None:
        await _mongo_client.close()
        _mongo_client = None
        logger.info("Connexion MongoDB fermee.")
