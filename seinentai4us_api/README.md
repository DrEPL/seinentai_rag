# 🎌 SEINENTAI4US API

API FastAPI complète pour la plateforme RAG **SEINENTAI4US** — groupe des jeunes.

---

## 📁 Structure du projet

```
seinentai4us_api/
├── api/
│   ├── main.py                    ← Point d'entrée FastAPI
│   ├── config.py                  ← Configuration centralisée (.env)
│   ├── routers/
│   │   ├── auth.py                ← POST /auth/*
│   │   ├── documents.py           ← GET|POST|DELETE /documents/*
│   │   ├── search.py              ← POST /search, GET /search/*
│   │   ├── chat.py                ← POST /chat/*, GET /chat/*
│   │   └── admin.py               ← GET /health
│   ├── models/
│   │   └── schemas.py             ← Modèles Pydantic (requêtes + réponses)
│   ├── services/
│   │   ├── auth_service.py        ← Gestion utilisateurs & tokens
│   │   ├── rag_service.py         ← Façade RAG (Ingestion + Retrieval + Génération)
│   │   └── chat_service.py        ← Gestion sessions de conversation
│   ├── dependencies/
│   │   └── auth.py                ← Dépendance get_current_user
│   └── middleware/
│       └── logging_middleware.py  ← Logging structuré des requêtes HTTP
├── tests/
│   └── test_api.py                ← Tests unitaires (pytest)
├── scripts/
│   └── SEINENTAI4US_API.postman_collection.json
├── data/                          ← Créé automatiquement (users, tokens, sessions)
├── requirements.txt
└── README.md
```

---

## ⚙️ Prérequis

| Service  | Version minimale | Port par défaut |
|----------|-----------------|-----------------|
| Python   | 3.11+           | —               |
| Qdrant   | 1.7+            | 6333            |
| MinIO    | RELEASE.2024+   | 9000            |
| Ollama   | 0.3+            | 11434           |
| Kafka    | 3.x (optionnel) | 9092            |

---

## 🚀 Installation

### 1. Placer l'API dans votre projet existant

```bash
# Copier le dossier seinentai4us_api/ à la racine de votre projet
# (au même niveau que Ingestion/, Retrieval/, Generation/, services/, utils/)

your_project/
├── seinentai4us_api/      ← (ce dossier)
├── Ingestion/
├── Retrieval/
├── Generation/
├── services/
├── utils/
└── .env
```

### 2. Installer les dépendances

```bash
cd seinentai4us_api
pip install -r requirements.txt
```

### 3. Configurer le `.env`

Copiez votre `.env` existant à la racine du projet (ou à la racine de `seinentai4us_api/`).
Les variables déjà présentes dans votre `.env` sont toutes reconnues.

Variables supplémentaires disponibles :

```env
# Auth
SECRET_KEY=changez-moi-en-production
TOKEN_EXPIRE_HOURS=24

# CORS (liste séparée par des virgules)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## ▶️ Lancement

### Développement (avec rechargement automatique)

```bash
# Depuis la racine du projet (parent de seinentai4us_api/)
uvicorn seinentai4us_api.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn seinentai4us_api.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

### Documentation interactive

- Swagger UI : http://localhost:8000/docs
- ReDoc      : http://localhost:8000/redoc

---

## 🧪 Tests

```bash
# Depuis la racine du projet
pytest seinentai4us_api/tests/test_api.py -v

# Avec couverture de code
pytest seinentai4us_api/tests/test_api.py -v --cov=seinentai4us_api/api --cov-report=html
```

---

## 📡 Endpoints

### 🔐 Authentification

| Méthode | Endpoint          | Description                         |
|---------|-------------------|-------------------------------------|
| POST    | `/auth/register`  | Créer un compte                     |
| POST    | `/auth/login`     | Connexion → retourne Bearer token   |
| POST    | `/auth/logout`    | Déconnexion (révocation du token)   |
| GET     | `/auth/me`        | Profil utilisateur connecté         |

**Utilisation du token :**
```bash
curl -H "Authorization: Bearer <votre_token>" http://localhost:8000/auth/me
```

---

### 📄 Documents

| Méthode | Endpoint                        | Description                            |
|---------|---------------------------------|----------------------------------------|
| POST    | `/documents/upload`             | Upload PDF → MinIO + indexation async  |
| GET     | `/documents`                    | Liste tous les documents               |
| GET     | `/documents/{filename}/status`  | Statut d'indexation                    |
| POST    | `/documents/reindex`            | Réindexer tout (ou une liste)          |
| DELETE  | `/documents/{filename}`         | Supprimer de MinIO + Qdrant            |

```bash
# Upload
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@mon_document.pdf"

# Statut
curl http://localhost:8000/documents/mon_document.pdf/status \
  -H "Authorization: Bearer $TOKEN"

# Réindexation forcée de fichiers spécifiques
curl -X POST http://localhost:8000/documents/reindex \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true, "filenames": ["doc1.pdf", "doc2.pdf"]}'
```

---

### 🔍 Recherche

| Méthode | Endpoint              | Description                          |
|---------|-----------------------|--------------------------------------|
| POST    | `/search`             | Recherche sémantique dense           |
| GET     | `/search/hybrid`      | Recherche hybride BM25 + dense       |
| GET     | `/search/rerank`      | Recherche + re-ranking par boosting  |

```bash
# Recherche sémantique
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "activités du groupe", "limit": 5, "score_threshold": 0.2}'

# Recherche hybride
curl "http://localhost:8000/search/hybrid?q=seinentai+valeurs&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Re-ranking (boost sur un fichier spécifique)
curl "http://localhost:8000/search/rerank?q=activités&boost_field=filename&boost_value=programme.pdf" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 💬 Chat

| Méthode | Endpoint                        | Description                                |
|---------|---------------------------------|--------------------------------------------|
| POST    | `/chat/new`                     | Nouveau chat (JSON direct ou SSE)          |
| POST    | `/chat/{session_id}`            | Continuer une session (SSE)                |
| GET     | `/chat/history`                 | Liste des sessions de l'utilisateur        |
| GET     | `/chat/sessions/{session_id}`   | Historique complet d'une session           |

```bash
# Nouveau chat direct
curl -X POST http://localhost:8000/chat/new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quelles sont les valeurs du groupe ?", "stream": false}'

# Nouveau chat en streaming SSE
curl -X POST http://localhost:8000/chat/new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Parle-moi des activités.", "stream": true}' \
  --no-buffer
```

**Format des événements SSE :**
```
data: {"type": "start", "session_id": "...", "sources": [...]}

data: {"type": "token", "token": "Le "}

data: {"type": "token", "token": "groupe "}

data: {"type": "done", "session_id": "...", "message_id": "..."}
```

---

### 🏥 Système

| Méthode | Endpoint   | Auth | Description                     |
|---------|------------|------|---------------------------------|
| GET     | `/health`  | Non  | Santé de tous les services      |

---

## 🔒 Sécurité

- **Rate limiting** : 200 requêtes/minute par IP (configurable via SlowAPI)
- **CORS** : configurable via `CORS_ORIGINS` dans `.env`
- **Tokens** : UUID v4 aléatoires, expiration configurable (`TOKEN_EXPIRE_HOURS`)
- **Mots de passe** : hachés HMAC-SHA256

> En production, remplacez le stockage JSON par PostgreSQL/Redis et définissez un `SECRET_KEY` fort.

---

## 🐳 Docker (optionnel)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r seinentai4us_api/requirements.txt
CMD ["uvicorn", "seinentai4us_api.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📬 Postman

Importez `scripts/SEINENTAI4US_API.postman_collection.json` dans Postman.

Le script de test de `/auth/login` sauvegarde automatiquement le token dans `{{token}}`
et le script de `/chat/new` sauvegarde le `session_id` dans `{{session_id}}`.

---

## 🛠️ Architecture & intégration

```
Client HTTP
    │
    ▼
FastAPI (api/main.py)
    │
    ├── /auth/*      → AuthService (api/services/auth_service.py)
    │                   └── Fichiers JSON (data/users.json, data/tokens.json)
    │
    ├── /documents/* → RAGService (api/services/rag_service.py)
    │                   ├── MinIOService  (services/minio_service.py)  [votre code]
    │                   ├── IngestionPipeline (Ingestion/)             [votre code]
    │                   └── VectorStore (Retrieval/vector_store.py)    [votre code]
    │
    ├── /search/*    → RAGService
    │                   └── RetrieverPipeline (Retrieval/)             [votre code]
    │
    ├── /chat/*      → RAGService + ChatSessionService
    │                   ├── RetrieverPipeline  [votre code]
    │                   ├── GenerationPipeline [votre code] → Ollama
    │                   └── Fichier JSON (data/chat_sessions.json)
    │
    └── /health      → Checks directs (Qdrant, MinIO, Ollama, Kafka)
```
