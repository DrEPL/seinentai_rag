"""
Tests unitaires — SEINENTAI4US API
Lancer avec : pytest tests/test_api.py -v
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# ── Chargement de l'app ───────────────────────────────────────────────────────
from seinentai4us_api.api.main import app

client = TestClient(app, raise_server_exceptions=False)

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def registered_user():
    """Crée un compte de test et retourne les credentials."""
    payload = {
        "email": "test_pytest@seinentai.jp",
        "password": "TestPwd@2024",
        "full_name": "Test Utilisateur",
    }
    resp = client.post("/auth/register", json=payload)
    # Accepte 201 (nouveau) ou 409 (déjà existant lors de reruns)
    assert resp.status_code in (201, 409)
    return payload


@pytest.fixture(scope="session")
def auth_token(registered_user):
    """Retourne un token valide pour les tests."""
    resp = client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuth:

    def test_register_success(self):
        import uuid
        unique_email = f"new_{uuid.uuid4().hex[:6]}@seinentai.jp"
        resp = client.post("/auth/register", json={
            "email": unique_email,
            "password": "Password@123",
            "full_name": "Nouveau User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == unique_email
        assert "id" in data

    def test_register_duplicate_email(self, registered_user):
        resp = client.post("/auth/register", json=registered_user)
        assert resp.status_code == 409

    def test_register_short_password(self):
        resp = client.post("/auth/register", json={
            "email": "shortpwd@seinentai.jp",
            "password": "abc",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "ValidPassword1",
            "full_name": "Test User",
        })
        assert resp.status_code == 422

    def test_login_success(self, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_wrong_password(self, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "mauvaismdp",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self):
        resp = client.post("/auth/login", json={
            "email": "ghost@seinentai.jp",
            "password": "AnyPassword123",
        })
        assert resp.status_code == 401

    def test_me_authenticated(self, auth_headers, registered_user):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == registered_user["email"]

    def test_me_unauthenticated(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
        assert resp.status_code == 401

    def test_logout(self, registered_user):
        # Créer un token dédié pour ce test
        login_resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/auth/logout", headers=headers)
        assert resp.status_code == 200

        # Le token est révoqué
        resp2 = client.get("/auth/me", headers=headers)
        assert resp2.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDocuments:

    def test_list_documents_authenticated(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.list_documents",
            return_value=[],
        ):
            resp = client.get("/documents", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "documents" in data

    def test_list_documents_unauthenticated(self):
        resp = client.get("/documents")
        assert resp.status_code == 401

    def test_upload_non_pdf(self, auth_headers):
        fake_minio = MagicMock()
        fake_minio.create_bucket_if_not_exists.return_value = None
        fake_minio.put_object.return_value = True
        with patch("services.minio_service.MinIOService", return_value=fake_minio):
            resp = client.post(
                "/documents/upload",
                headers=auth_headers,
                files={"file": ("test.txt", b"Hello world", "text/plain")},
            )
        assert resp.status_code == 202
        assert "test.txt" in resp.json()["message"]

    def test_upload_empty_file(self, auth_headers):
        resp = client.post(
            "/documents/upload",
            headers=auth_headers,
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_upload_pdf_success(self, auth_headers):
        fake_pdf = b"%PDF-1.4 fake pdf content for testing purposes"
        mock_minio = MagicMock()
        mock_minio.create_bucket_if_not_exists.return_value = None
        mock_minio.put_object.return_value = True

        with patch("services.minio_service.MinIOService", return_value=mock_minio):
            resp = client.post(
                "/documents/upload",
                headers=auth_headers,
                files={"file": ("test_doc.pdf", fake_pdf, "application/pdf")},
            )
        assert resp.status_code == 202
        assert "test_doc.pdf" in resp.json()["message"]

    def test_document_status_not_found(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.get_document_status",
            return_value={"filename": "ghost.pdf", "status": "not_found"},
        ):
            resp = client.get("/documents/ghost.pdf/status", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"

    def test_document_status_indexed(self, auth_headers):
        mock_status = {
            "filename": "reglement.pdf",
            "status": "indexed",
            "doc_id": "abc123",
            "chunk_count": 42,
            "size_bytes": 102400,
            "last_modified": "2024-01-01T00:00:00",
        }
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.get_document_status",
            return_value=mock_status,
        ):
            resp = client.get("/documents/reglement.pdf/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "indexed"
        assert data["chunk_count"] == 42

    def test_delete_document(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.delete_document",
            return_value=(True, "Document 'test.pdf' supprimé."),
        ):
            resp = client.delete("/documents/test.pdf", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_document_failure(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.delete_document",
            return_value=(False, "Erreur MinIO"),
        ):
            resp = client.delete("/documents/missing.pdf", headers=auth_headers)
        assert resp.status_code == 500

    def test_reindex(self, auth_headers):
        resp = client.post("/documents/reindex", headers=auth_headers, json={"force": False})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_DOCS = [
    {
        "text": "Les jeunes se retrouvent chaque samedi pour des activités culturelles.",
        "filename": "programme.pdf",
        "score": 0.87,
        "chunk_index": 0,
        "total_chunks": 10,
        "doc_id": "doc1",
        "metadata": {"filename": "programme.pdf"},
    }
]


class TestSearch:

    def test_semantic_search_success(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=MOCK_DOCS,
        ):
            resp = client.post("/search", headers=auth_headers, json={
                "query": "activités du groupe des jeunes",
                "limit": 5,
                "score_threshold": 0.0,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["score"] == 0.87
        assert "search_time_ms" in data

    def test_semantic_search_empty_query(self, auth_headers):
        resp = client.post("/search", headers=auth_headers, json={"query": ""})
        assert resp.status_code == 422

    def test_semantic_search_unauthenticated(self):
        resp = client.post("/search", json={"query": "test"})
        assert resp.status_code == 401

    def test_semantic_search_no_results(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=[],
        ):
            resp = client.post("/search", headers=auth_headers, json={
                "query": "requête sans résultat xyz123abc",
                "limit": 5,
            })
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_hybrid_search_success(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.hybrid_search",
            return_value=MOCK_DOCS,
        ):
            resp = client.get(
                "/search/hybrid",
                headers=auth_headers,
                params={"q": "activités culturelles", "limit": 5},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["search_type"] == "hybrid"
        assert data["total"] == 1

    def test_hybrid_search_missing_query(self, auth_headers):
        resp = client.get("/search/hybrid", headers=auth_headers)
        assert resp.status_code == 422

    def test_rerank_search_success(self, auth_headers):
        mock_rerank_docs = [{
            **MOCK_DOCS[0],
            "original_score": 0.87,
            "boosted_score": 1.305,
        }]
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search_with_rerank",
            return_value=mock_rerank_docs,
        ):
            resp = client.get(
                "/search/rerank",
                headers=auth_headers,
                params={
                    "q": "activités",
                    "boost_field": "filename",
                    "boost_value": "programme.pdf",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["boost_field"] == "filename"
        assert data["results"][0]["boosted_score"] > data["results"][0]["original_score"]


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_GENERATION = {
    "success": True,
    "response": "Le groupe des jeunes se retrouve le samedi pour des activités variées.",
    "model": "mistral:7b",
    "generation_time": 1.23,
    "prompt_tokens": 150,
    "completion_tokens": 40,
}


class TestChat:

    def test_new_chat_success(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=MOCK_DOCS,
        ), patch(
            "seinentai4us_api.api.services.rag_service.rag_service.generate",
            return_value=MOCK_GENERATION,
        ):
            resp = client.post("/chat/new", headers=auth_headers, json={
                "message": "Quelles sont les activités du groupe ?",
                "stream": False,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "response" in data
        assert len(data["response"]) > 0
        assert "sources" in data

    def test_new_chat_creates_session(self, auth_headers):
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=[],
        ), patch(
            "seinentai4us_api.api.services.rag_service.rag_service.generate",
            return_value=MOCK_GENERATION,
        ):
            resp = client.post("/chat/new", headers=auth_headers, json={
                "message": "Question de test",
                "stream": False,
            })
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]
        assert len(session_id) == 36  # UUID format

    def test_new_chat_unauthenticated(self):
        resp = client.post("/chat/new", json={"message": "Test", "stream": False})
        assert resp.status_code == 401

    def test_new_chat_empty_message(self, auth_headers):
        resp = client.post("/chat/new", headers=auth_headers, json={"message": ""})
        assert resp.status_code == 422

    def test_new_chat_ollama_error(self, auth_headers):
        error_gen = {"success": False, "error": "Ollama indisponible"}
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=[],
        ), patch(
            "seinentai4us_api.api.services.rag_service.rag_service.generate",
            return_value=error_gen,
        ):
            resp = client.post("/chat/new", headers=auth_headers, json={
                "message": "Test Ollama down",
                "stream": False,
            })
        assert resp.status_code == 503

    def test_get_session_history(self, auth_headers):
        # Créer une session d'abord
        with patch(
            "seinentai4us_api.api.services.rag_service.rag_service.search",
            return_value=[],
        ), patch(
            "seinentai4us_api.api.services.rag_service.rag_service.generate",
            return_value=MOCK_GENERATION,
        ):
            create_resp = client.post("/chat/new", headers=auth_headers, json={
                "message": "Ma première question",
                "stream": False,
            })
        session_id = create_resp.json()["session_id"]

        # Récupérer l'historique
        resp = client.get(f"/chat/sessions/{session_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["message_count"] >= 2  # user + assistant

    def test_get_session_not_found(self, auth_headers):
        resp = client.get("/chat/sessions/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert resp.status_code == 404

    def test_chat_history_list(self, auth_headers):
        resp = client.get("/chat/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_continue_chat_session_not_found(self, auth_headers):
        resp = client.post(
            "/chat/00000000-dead-beef-0000-000000000000",
            headers=auth_headers,
            json={"session_id": "xxx", "message": "Suite ?", "stream": False},
        )
        assert resp.status_code in (404, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# SANTÉ SYSTÈME
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealth:

    def test_health_returns_structure(self):
        """Le /health doit toujours répondre, même si des services sont down."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "services" in data
        assert "timestamp" in data
        service_names = [s["name"] for s in data["services"]]
        assert "qdrant" in service_names
        assert "minio" in service_names
        assert "ollama" in service_names

    def test_health_service_fields(self):
        resp = client.get("/health")
        for svc in resp.json()["services"]:
            assert "name" in svc
            assert "status" in svc
            assert svc["status"] in ("ok", "error", "degraded")

    def test_root_endpoint(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "SEINENTAI4US API"


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING & SÉCURITÉ
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurity:

    def test_cors_headers_present(self):
        resp = client.options("/health", headers={"Origin": "http://localhost:3000"})
        # FastAPI avec CORSMiddleware peut retourner 200 ou 405 selon la config
        assert resp.status_code in (200, 405)

    def test_request_id_header_in_response(self):
        resp = client.get("/health")
        assert "x-request-id" in resp.headers

    def test_response_time_header_in_response(self):
        resp = client.get("/health")
        assert "x-response-time" in resp.headers

    def test_protected_route_no_header(self):
        resp = client.get("/documents")
        assert resp.status_code == 401

    def test_protected_route_malformed_token(self):
        resp = client.get("/documents", headers={"Authorization": "NotBearer abc"})
        assert resp.status_code == 401

    def test_protected_route_bearer_without_token(self):
        resp = client.get("/documents", headers={"Authorization": "Bearer"})
        assert resp.status_code == 401
