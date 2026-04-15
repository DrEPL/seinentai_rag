"""Service de suivi des documents indexes (MinIO + Qdrant)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from seinentai4us_api.api.db.models import IndexedDocument


class DocumentRegistryService:
    async def upsert_uploaded_document(
        self,
        *,
        filename: str,
        bucket: str,
        object_key: str,
        size_bytes: int,
        content_type: str,
        uploaded_by: str,
        minio_etag: Optional[str] = None,
    ) -> IndexedDocument:
        now = datetime.utcnow()
        existing = await IndexedDocument.find_one(
            IndexedDocument.filename == filename,
            IndexedDocument.bucket == bucket,
        )
        if existing:
            existing.object_key = object_key
            existing.size_bytes = size_bytes
            existing.content_type = content_type
            existing.uploaded_by = uploaded_by
            existing.minio_etag = minio_etag
            existing.status = "uploaded"
            existing.updated_at = now
            await existing.save()
            return existing

        doc = IndexedDocument(
            document_id=str(uuid.uuid4()),
            filename=filename,
            bucket=bucket,
            object_key=object_key,
            size_bytes=size_bytes,
            content_type=content_type,
            uploaded_by=uploaded_by,
            minio_etag=minio_etag,
            status="uploaded",
            created_at=now,
            updated_at=now,
        )
        await doc.insert()
        return doc

    async def mark_deleted(self, *, filename: str, bucket: str) -> None:
        doc = await IndexedDocument.find_one(
            IndexedDocument.filename == filename,
            IndexedDocument.bucket == bucket,
        )
        if doc:
            doc.status = "deleted"
            doc.updated_at = datetime.utcnow()
            await doc.save()


document_registry_service = DocumentRegistryService()
