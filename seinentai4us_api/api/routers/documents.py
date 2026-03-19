"""
Router Documents — SEINENTAI4US
POST /documents/upload | DELETE /documents/{filename}
GET  /documents         | GET /documents/{filename}/status
POST /documents/reindex
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from seinentai4us_api.api.config import settings
from seinentai4us_api.api.dependencies.auth import get_current_user
from seinentai4us_api.api.models.schemas import (
    DocumentListResponse,
    DocumentStatus,
    MessageResponse,
    ReindexRequest,
    ReindexResponse,
    UserProfile,
)
from seinentai4us_api.api.services.rag_service import rag_service
from seinentai4us_api.utils.functions import normalize_filename

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Upload ───────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload d'un document",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Fichier supporté à indexer"),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Upload un document supporté vers MinIO puis le passe dans le pipeline d'indexation.

    L'indexation est effectuée en tâche de fond — utilisez `GET /documents/{filename}/status`
    pour vérifier la progression.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier manquant.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.SUPPORTED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensions supportées : {', '.join(settings.SUPPORTED_DOCUMENT_EXTENSIONS)}.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier est vide.",
        )
        
    normalized_filename = normalize_filename(file.filename)

    # Upload vers MinIO
    try:
        minio = rag_service.get_minio_client()
        minio.create_bucket_if_not_exists(settings.MINIO_BUCKET)
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown",
            ".markdown": "text/markdown",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
        }
        content_type = mime_map.get(ext, "application/octet-stream")
        ok = minio.put_object(settings.MINIO_BUCKET, normalized_filename, content, content_type)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de l'upload vers MinIO.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur MinIO : {e}")

    # Indexation en tâche de fond
    def _index(bucket: str, filename: str):
        success, msg = rag_service.ingest_document(bucket, filename)
        if success:
            logger.info(f"✅ Indexation en arrière-plan : {filename}")
        else:
            logger.error(f"❌ Échec indexation {filename} : {msg}")

    # background_tasks.add_task(_index, settings.MINIO_BUCKET, file.filename)

    return MessageResponse(
        message=f"Document '{file.filename}' uploadé.",
    )


# ─── Suppression ──────────────────────────────────────────────────────────────

@router.delete(
    "/{filename}",
    response_model=MessageResponse,
    summary="Supprimer un document (MinIO + Qdrant)",
)
async def delete_document(
    filename: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Supprime le document de MinIO et tous ses chunks de Qdrant."""
    success, msg = rag_service.delete_document(filename)
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return MessageResponse(message=msg)


# ─── Listing ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Lister tous les documents indexés",
)
async def list_documents(current_user: UserProfile = Depends(get_current_user)):
    """Retourne la liste des documents présents dans MinIO avec leur statut d'indexation."""
    docs = rag_service.list_documents()
    return DocumentListResponse(total=len(docs), documents=docs)


# ─── Statut ───────────────────────────────────────────────────────────────────

@router.get(
    "/{filename}/status",
    response_model=DocumentStatus,
    summary="Statut d'indexation d'un document",
)
async def document_status(
    filename: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Retourne le statut d'indexation d'un document :
    - `indexed` : présent dans Qdrant
    - `pending` : présent dans MinIO mais pas encore indexé
    - `not_found` : absent de MinIO
    - `error` : erreur lors de la vérification
    """
    status_data = rag_service.get_document_status(filename)
    return DocumentStatus(**status_data)


# ─── Réindexation ─────────────────────────────────────────────────────────────

@router.post(
    "/reindex",
    response_model=ReindexResponse,
    summary="Réindexer tous les documents (ou une liste)",
)
async def reindex_documents(
    body: ReindexRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Relance le pipeline d'indexation sur tous les documents MinIO (ou une liste explicite).

    - **force** : si `true`, réindexe même les documents déjà indexés
    - **filenames** : liste facultative de fichiers spécifiques
    """
    def _do_reindex():
        result = rag_service.reindex_all(force=body.force, filenames=body.filenames)
        logger.info(f"Réindexation terminée : {result['success']}/{result['total']} succès")

    background_tasks.add_task(_do_reindex)

    # Retour immédiat avec estimation
    return ReindexResponse(
        total=0,
        success=0,
        skipped=0,
        failed=0,
        details=[{"message": "Réindexation démarrée en arrière-plan."}],
    )
