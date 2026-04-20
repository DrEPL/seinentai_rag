"""
Service RAG — SEINENTAI4US
Wrapper autour des pipelines existants (Ingestion, Retrieval, Generation).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from qdrant_client.http import models
from seinentai4us_api.api.config import settings

logger = logging.getLogger(__name__)


# ─── Lazy singletons (initialisés au premier appel) ──────────────────────────
_retriever_pipeline = None
_generation_pipeline = None


def _get_retriever():
    global _retriever_pipeline
    if _retriever_pipeline is None:
        from Retrieval.retrieval_pipeline import RetrieverPipeline
        _retriever_pipeline = RetrieverPipeline()
    return _retriever_pipeline


def _get_generator():
    global _generation_pipeline
    if _generation_pipeline is None:
        from Generation.generation import GenerationPipeline
        _generation_pipeline = GenerationPipeline()
    return _generation_pipeline


def initialize_pipelines(*, retriever_pipeline=None, generation_pipeline=None) -> None:
    """
    Permet au `lifespan` de fournir des singletons déjà initialisés.

    Utile pour éviter toute recréation (embeddings / clients Qdrant / MinIO) au premier appel.
    """
    global _retriever_pipeline, _generation_pipeline
    if retriever_pipeline is not None:
        _retriever_pipeline = retriever_pipeline
    if generation_pipeline is not None:
        _generation_pipeline = generation_pipeline


class RAGService:
    """Façade unifiée pour toutes les opérations RAG."""

    def get_minio_client(self):
        """
        Retourne le client MinIO utilisé par le retriever.

        Si le retriever n'a pas été initialisé (ex: tests), on retombe sur une instanciation locale
        pour conserver la compatibilité.
        """
        global _retriever_pipeline
        if _retriever_pipeline is not None and hasattr(_retriever_pipeline, "minio_client"):
            return _retriever_pipeline.minio_client

        from services.minio_service import MinIOService

        return MinIOService()

    # ── Documents ─────────────────────────────────────────────────────────────

    def ingest_document(self, bucket: str, filename: str) -> Tuple[bool, str]:
        """Ingère et indexe un document depuis MinIO."""
        try:
            retriever = _get_retriever()
            success = retriever.process_document(bucket=bucket, filename=filename)
            if success:
                return True, f"Document '{filename}' indexé avec succès."
            return False, f"Échec de l'indexation de '{filename}'."
        except Exception as e:
            logger.error(f"Erreur ingest_document {filename}: {e}")
            return False, str(e)

    def delete_document(self, filename: str) -> Tuple[bool, str]:
        """Supprime un document de MinIO ET de Qdrant."""
        try:
            retriever = _get_retriever()
            minio = retriever.minio_client
            vector_store = retriever.vector_store

            # Supprimer de MinIO
            minio.delete_object(settings.MINIO_BUCKET, filename)

            # Supprimer de Qdrant (tous les chunks du fichier)
            vector_store.client.delete(
                collection_name=vector_store.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="filename",
                                match=models.MatchValue(value=filename),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"🗑️ Document '{filename}' supprimé de MinIO et Qdrant.")
            return True, f"Document '{filename}' supprimé."
        except Exception as e:
            logger.error(f"Erreur delete_document {filename}: {e}")
            return False, str(e)

    def list_documents(self) -> List[Dict[str, Any]]:
        """Liste les documents dans MinIO avec leur statut d'indexation."""
        try:
            retriever = _get_retriever()
            minio = retriever.minio_client
            objects = minio.list_objects(settings.MINIO_BUCKET)

            # Récupérer les docs indexés depuis Qdrant
            indexed = self._get_indexed_filenames()
            chunk_counts = self._get_chunk_counts()

            result = []
            for obj in objects:
                fname = obj["filename"]
                result.append({
                    **obj,
                    "indexed": fname in indexed,
                    "chunk_count": chunk_counts.get(fname, 0) if fname in indexed else None,
                })
            return result
        except Exception as e:
            logger.error(f"Erreur list_documents: {e}")
            return []

    def get_document_status(self, filename: str) -> Dict[str, Any]:
        """Retourne le statut d'indexation d'un document."""
        try:
            from qdrant_client.http import models

            retriever = _get_retriever()
            minio = retriever.minio_client
            vector_store = retriever.vector_store
            meta = minio.get_object_metadata(settings.MINIO_BUCKET, filename)
            if not meta:
                return {"filename": filename, "status": "not_found"}

            results, _ = vector_store.client.scroll(
                collection_name=vector_store.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="filename",
                            match=models.MatchValue(value=filename),
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
            )

            if results:
                doc_id = results[0].payload.get("doc_id")
                return {
                    "filename": filename,
                    "status": "indexed",
                    "doc_id": doc_id,
                    "chunk_count": len(results),
                    "size_bytes": meta.get("size"),
                    "last_modified": meta.get("last_modified"),
                }
            return {
                "filename": filename,
                "status": "pending",
                "size_bytes": meta.get("size"),
                "last_modified": meta.get("last_modified"),
            }
        except Exception as e:
            logger.error(f"Erreur get_document_status {filename}: {e}")
            return {"filename": filename, "status": "error", "error": str(e)}

    def reindex_all(self, force: bool = False, filenames: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Réindexe les documents selon les paramètres.
        
        Args:
            force: 
                - False: ne réindexe que les documents non encore indexés
                - True: supprime les anciennes versions avant réindexation
            filenames:
                - None: traite tous les documents du bucket MinIO
                - Liste: traite uniquement les fichiers spécifiés
        
        Returns:
            Dict contenant les statistiques de l'opération:
            - total: nombre total de documents traités
            - success: nombre de documents indexés avec succès
            - skipped: nombre de documents ignorés
            - failed: nombre d'échecs
            - details: liste détaillée par document
        
        Examples:
            >>> # Cas 1: Indexer uniquement les nouveaux documents
            >>> pipeline.reindex_all()
            
            >>> # Cas 2: Réindexation complète (vider puis tout réindexer)
            >>> pipeline.reindex_all(force=True)
            
            >>> # Cas 3: Ajouter des fichiers spécifiques (sans forcer)
            >>> pipeline.reindex_all(filenames=["doc1.pdf", "doc2.pdf"])
            
            >>> # Cas 4: Forcer la mise à jour de fichiers spécifiques
            >>> pipeline.reindex_all(force=True, filenames=["doc1.pdf"])
        """
        retriever = _get_retriever()
        minio = retriever.minio_client
        vector_store = retriever.vector_store
        
        # Récupération des documents à traiter
        if filenames:
            objects = [{"filename": f} for f in filenames]
        else:
            objects = minio.list_objects(settings.MINIO_BUCKET)
        
        total = len(objects)
        success = skipped = failed = 0
        details = []
        
        print(f"🚀 Début de réindexation: {total} documents à traiter (force={force})")
        
        # Cas spécial: réindexation complète avec force=True
        if force and not filenames:
            print("🗑️ Suppression massive de la collection...")
            try:
                vector_store.client.delete(
                    collection_name=vector_store.collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(must=[])  # Supprime tout
                    ),
                )
                print("✅ Collection vidée avec succès")
            except Exception as e:
                print(f"⚠️ Erreur lors du vidage: {e}")
                # On continue quand même ?
        
        for idx, obj in enumerate(objects, 1):
            fname = obj["filename"]
            ext = Path(fname).suffix.lower()
            
            print(f"📄 [{idx}/{total}] Traitement de: {fname}")
            
            # Vérification extension
            if ext not in settings.SUPPORTED_DOCUMENT_EXTENSIONS:
                skipped += 1
                details.append({
                    "filename": fname,
                    "result": "skipped",
                    "reason": f"unsupported_extension ({ext})",
                })
                print(f"   ⏭️ Extension non supportée: {ext}")
                continue
            
            # Vérification statut (sauf si force=True)
            if not force:
                status = self.get_document_status(fname)
                if status.get("status") == "indexed":
                    skipped += 1
                    details.append({
                        "filename": fname,
                        "result": "skipped",
                        "reason": "already_indexed"
                    })
                    print(f"   ⏭️ Déjà indexé (use force=True to reindex)")
                    continue
            
            # Suppression des anciens chunks (sauf si déjà fait en masse)
            if not (force and not filenames):  # Si pas de suppression massive
                try:
                    vector_store.client.delete(
                        collection_name=vector_store.collection_name,
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="filename",
                                        match=models.MatchValue(value=fname),
                                    )
                                ]
                            )
                        ),
                    )
                    print(f"   🗑️ Anciens chunks supprimés")
                except Exception as e:
                    print(f"   ⚠️ Erreur suppression: {e}")
                    # On continue quand même ?
            
            # Ingestion du document
            try:
                ok, msg = self.ingest_document(settings.MINIO_BUCKET, fname)
                if ok:
                    success += 1
                    details.append({
                        "filename": fname,
                        "result": "success",
                        "message": msg
                    })
                    print(f"   ✅ Succès")
                else:
                    failed += 1
                    details.append({
                        "filename": fname,
                        "result": "failed",
                        "reason": msg
                    })
                    print(f"   ❌ Échec: {msg}")
            except Exception as e:
                failed += 1
                details.append({
                    "filename": fname,
                    "result": "failed",
                    "reason": str(e),
                    "error_type": type(e).__name__
                })
                print(f"   ❌ Exception: {e}")
                import traceback
                traceback.print_exc()
        
        # Résumé final
        print(f"\n{'='*50}")
        print(f"📊 RÉSULTATS DE LA RÉINDEXATION")
        print(f"{'='*50}")
        print(f"📝 Total: {total}")
        print(f"✅ Succès: {success}")
        print(f"⏭️ Ignorés: {skipped}")
        print(f"❌ Échecs: {failed}")
        print(f"{'='*50}")
        
        return {"total": total, "success": success, "skipped": skipped, "failed": failed, "details": details}

    # ── Recherche ─────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.0,
        filename_filter: Optional[str] = None,
        use_hybrid: bool = False,
        use_hyde: bool = False,
    ) -> List[Dict[str, Any]]:
        """Recherche sémantique dense."""
        try:
            retriever = _get_retriever()
            filter_condition = {"filename": filename_filter} if filename_filter else None
            results = retriever.search(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                use_hybrid=use_hybrid,
                use_hyde=use_hyde,
            )
            if filename_filter:
                results = [r for r in results if r.get("filename") == filename_filter]
            return results
        except Exception as e:
            logger.error(f"Erreur search: {e}")
            return []

    def hybrid_search(self, query: str, limit: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Recherche hybride BM25 + dense."""
        return self.search(query, limit, score_threshold, use_hybrid=True)

    # def search_with_rerank(
    #     self,
    #     query: str,
    #     boost_field: str,
    #     boost_value: Any,
    #     limit: int = 10,
    #     score_threshold: float = 0.0,
    # ) -> List[Dict[str, Any]]:
    #     """Recherche dense + re-ranking par score boosting sur un champ métadonnée."""
    #     results = self.search(query, limit=limit * 2, score_threshold=score_threshold)

    #     BOOST_FACTOR = 1.5
    #     for r in results:
    #         original_score = r.get("score", 0.0)
    #         meta_val = r.get("metadata", {}).get(boost_field) or r.get(boost_field)
    #         boosted = original_score * BOOST_FACTOR if str(meta_val) == str(boost_value) else original_score
    #         r["original_score"] = original_score
    #         r["boosted_score"] = boosted

    #     results.sort(key=lambda x: x["boosted_score"], reverse=True)
    #     return results[:limit]

    # ── Génération ────────────────────────────────────────────────────────────

    def generate(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        template: Optional[str] = None,
        stream: bool = False,
        stream_callback=None,
    ) -> Dict[str, Any]:
        """Génère une réponse RAG via Ollama."""
        generator = _get_generator()
        return generator.generate(
            query=query,
            retrieved_docs=retrieved_docs,
            template_name=template,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            callback=stream_callback,
        )

    def generate_stream(self, query: str, retrieved_docs: List[Dict[str, Any]], **kwargs):
        """Génère un flux SSE via Ollama en mode streaming direct."""
        import requests
        from seinentai4us_api.utils.functions import build_prompt, format_context

        generator = _get_generator()
        context = format_context(retrieved_docs)
        prompt = build_prompt(generator, query, context, kwargs.get("template"))

        request_body = {
            "model": generator.model_name,
            "prompt": prompt,
            "system": generator.system_prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature") or float(settings.DEFAULT_TEMPERATURE),
                "num_predict": kwargs.get("max_tokens") or int(settings.DEFAULT_MAX_TOKENS),
            },
        }

        with requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=request_body,
            stream=True,
            timeout=180,
        ) as resp:
            import json as _json
            for line in resp.iter_lines():
                if line:
                    chunk = _json.loads(line)
                    token = chunk.get("response", "")
                    done = chunk.get("done", False)
                    yield token, done
                    if done:
                        break

    # ── Utilitaires privées ───────────────────────────────────────────────────

    def _get_indexed_filenames(self) -> set:
        try:
            retriever = _get_retriever()
            client = retriever.vector_store.client
            results, _ = client.scroll(
                collection_name=retriever.vector_store.collection_name,
                with_payload=True,
                limit=10000,
            )
            return {r.payload.get("filename") for r in results if r.payload.get("filename")}
        except Exception:
            return set()

    def _get_chunk_counts(self) -> Dict[str, int]:
        try:
            retriever = _get_retriever()
            client = retriever.vector_store.client
            results, _ = client.scroll(
                collection_name=retriever.vector_store.collection_name,
                with_payload=True,
                limit=10000,
            )
            counts: Dict[str, int] = {}
            for r in results:
                fname = r.payload.get("filename")
                if fname:
                    counts[fname] = counts.get(fname, 0) + 1
            return counts
        except Exception:
            return {}


rag_service = RAGService()
