# 🤖 SEINENTAI RAG — Agent RAG Intelligent

> Système RAG (Retrieval-Augmented Generation) agentique pour **Sukyo Mahikari**, propulsé par **LangGraph** et **Mistral Large 3**.

---

## 🎯 Vue d'ensemble

SEINENTAI RAG est un système de question-réponse intelligent qui combine retrieval documentaire et génération par LLM. Contrairement aux pipelines RAG statiques, il utilise un **agent autonome** capable de :

- **Analyser** chaque requête (type, complexité, domaine)
- **Choisir dynamiquement** la stratégie de recherche optimale
- **Décomposer** les questions complexes en sous-requêtes
- **Évaluer la qualité** du contexte récupéré et **itérer** si nécessaire
- **Streamer ses pensées** en temps réel via SSE

```
┌─────────────────────────────────────────────────────────┐
│                   SEINENTAI RAG AGENT                   │
│                                                         │
│  Query ──▶ Analyze ──▶ Route ──▶ Search ──▶ Rerank     │
│                                      │                  │
│           ◀── Fallback ◀── Evaluate ◀┘                  │
│                                 │                       │
│                          Synthesize ──▶ Response         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### Stack technique

| Composant | Technologie |
|---|---|
| **Orchestration Agent** | LangGraph (StateGraph) |
| **LLM** | Mistral Large 3 (675B, Cloud) via Ollama |
| **API** | FastAPI |
| **Recherche vectorielle** | Qdrant |
| **Stockage documents** | MinIO (S3-compatible) |
| **Historique conversations** | MongoDB |
| **Message Queue** | Kafka |
| **Embeddings** | Modèle configurable via `.env` |
| **Reranking** | Cross-Encoder (sentence-transformers) |

### Modes de retrieval

L'agent choisit automatiquement parmi 3 stratégies :

| Stratégie | Quand l'utiliser | Outil |
|---|---|---|
| **Dense Search** | Requêtes bien formulées, spécifiques | `dense_search` |
| **Hybrid Search** | Termes techniques, noms propres, acronymes | `hybrid_search` |
| **HyDE Search** | Questions conceptuelles, abstraites | `hyde_search` |

> ⚠️ L'agent ne combine **jamais** HyDE et Hybrid Search simultanément (contre-productif).

---

## 📁 Structure du projet

```
seinentai_rag/
├── Agent/                          # 🤖 Agent RAG intelligent (LangGraph)
│   ├── __init__.py
│   ├── state.py                    # AgentState — état partagé du graphe
│   ├── tools.py                    # Outils de retrieval (dense, hybrid, hyde, rerank)
│   ├── prompts.py                  # Prompts spécialisés (analyse, évaluation, synthèse)
│   └── graph.py                    # StateGraph LangGraph (7 nœuds)
│
├── Generation/                     # 📝 Pipeline de génération LLM
│   └── generation.py
│
├── Ingestion/                      # 📥 Pipeline d'ingestion documentaire
│   ├── document_processor.py
│   ├── text_chunker.py
│   └── ingestion_pipeline.py
│
├── Retrieval/                      # 🔍 Moteurs de recherche
│   ├── vector_store.py             # Qdrant adapter
│   ├── hybrid_retriever.py         # Dense + BM25 fusion
│   ├── cross_encoder_reranker.py   # Cross-encoder reranking
│   └── retriever_pipeline.py       # Pipeline de retrieval orchestré
│
├── seinentai4us_api/               # 🌐 API FastAPI
│   ├── api/
│   │   ├── main.py                 # Point d'entrée & lifespan
│   │   ├── config.py               # Configuration centralisée
│   │   ├── routers/
│   │   │   ├── chat.py             # Endpoints /chat (agent + statique)
│   │   │   ├── documents.py        # Endpoints /documents
│   │   │   └── search.py           # Endpoints /search
│   │   ├── models/
│   │   │   └── schemas.py          # Schémas Pydantic
│   │   └── services/
│   │       ├── agentic_rag_service.py  # Service agent (run + stream)
│   │       ├── rag_service.py          # Service RAG statique
│   │       └── app_services.py         # Initialisation des services
│   └── utils/
│       └── functions.py            # Utilitaires (prompts, formatting)
│
├── services/                       # 🔄 Services background
│   └── kafka_consumer.py           # Consumer Kafka pour indexation async
│
├── containers/                     # 🐳 Docker
│
├── .env                            # Variables d'environnement
├── requirements.txt                # Dépendances Python
├── start_container.py              # Script de démarrage des conteneurs
└── TEST_README.md                  # Documentation des tests pipeline
```

---

## ⚡ Démarrage rapide

### 1. Prérequis

- **Python 3.11+**
- **Docker & Docker Compose**
- Accès au modèle **Mistral Large 3** (via Ollama Cloud)

### 2. Installation

```bash
# Cloner le projet
git clone <repo-url>
cd seinentai_rag

# Environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

Copier et adapter le fichier `.env` :

```env
# LLM
OLLAMA_MODEL_NAME=mistral-large-3:675b-cloud
OLLAMA_BASE_URL=http://ollama:11434

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=seinentai_documents

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=seinentai-documents

# MongoDB
MONGODB_URI=mongodb://root:example@localhost:27017
MONGODB_DATABASE=seinentai_db
```

### 4. Démarrer les services

```bash
# Démarrer tous les conteneurs (Qdrant, MinIO, MongoDB, Kafka)
python start_container.py

# Ou directement avec Docker Compose
docker-compose up -d
```

### 5. Lancement

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

L'API est accessible sur `http://localhost:8000`. Documentation interactive : `http://localhost:8000/docs`.

---

## 🔌 API Endpoints

### Chat (mode agent)

```http
POST /chat/new
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "Quelles sont les valeurs du groupe des jeunes ?",
    "stream": true,
    "use_agent": true
}
```

### Paramètres

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `message` | `string` | *(requis)* | Question de l'utilisateur |
| `stream` | `bool` | `false` | Activer le streaming SSE |
| `use_agent` | `bool` | `true` | Mode agent intelligent (vs. pipeline statique) |
| `use_hybrid` | `bool` | `false` | *(mode statique)* Forcer la recherche hybride |
| `use_hyde` | `bool` | `false` | *(mode statique)* Forcer HyDE |
| `temperature` | `float` | `0.7` | Température de génération |
| `search_limit` | `int` | `5` | Nombre de chunks à récupérer |

### Réponse (mode agent, non-streaming)

```json
{
    "session_id": "abc123",
    "message_id": "def456",
    "response": "Les valeurs du groupe des jeunes comprennent...",
    "sources": [
        {
            "filename": "document.pdf",
            "score": 0.8542,
            "chunk_index": 3,
            "excerpt": "..."
        }
    ],
    "model": "agent-langgraph",
    "generation_time": 4.2,
    "agent_trace": {
        "query_type": "simple",
        "strategies_tried": ["dense"],
        "iterations": 1,
        "quality_score": 0.85,
        "thoughts": [...],
        "tool_calls": [...]
    }
}
```

---

## 📡 Streaming SSE — Événements

Quand `stream=true` et `use_agent=true`, l'API retourne un flux `text/event-stream` avec les événements suivants :

| Type | Description | Contenu |
|---|---|---|
| `start` | Début de la requête | `session_id`, `mode: "agent"` |
| `thought` | Raisonnement de l'agent | `node`, `content` |
| `tool_call` | Appel d'un outil de recherche | `tool`, `params`, `result_preview` |
| `observation` | Résultat d'évaluation qualité | Score, suffisance, feedback |
| `synthesis_start` | Début de la génération | — |
| `token` | Réponse générée | Texte de la réponse |
| `done` | Fin de la requête | `sources`, `agent_trace` |
| `error` | Erreur | `message` |

### Exemple de flux SSE

```
data: {"type": "start", "session_id": "abc123", "mode": "agent"}

data: {"type": "thought", "node": "analyze_query", "content": "Type: simple | Stratégie: dense | Raison: Requête directe et spécifique"}

data: {"type": "tool_call", "tool": "dense_search", "params": {"limit": 10}, "result_preview": "[dense_search] 8 documents trouvés..."}

data: {"type": "thought", "node": "rerank_results", "content": "Reranking de 8 documents"}

data: {"type": "observation", "content": "Qualité: 0.82 — ✅ Suffisant — Bonne couverture thématique"}

data: {"type": "synthesis_start"}

data: {"type": "token", "token": "Les valeurs du groupe des jeunes..."}

data: {"type": "done", "sources": [...], "agent_trace": {...}}
```

---

## 🧠 Graphe de l'Agent (LangGraph)

```mermaid
graph TD
    A["🔍 analyze_query"] -->|complex / multi-hop| B["🔀 decompose_query"]
    A -->|simple / direct| C["📚 execute_search"]
    B --> C
    C --> D["📊 rerank_results"]
    D --> E["✅ evaluate_quality"]
    E -->|"quality ≥ 0.6"| F["📝 synthesize_response"]
    E -->|"quality < 0.6"| G["🔄 handle_fallback"]
    G -->|retry| C
    G -->|max iterations| F
    F --> H["🏁 END"]
```

### Nœuds

| Nœud | Rôle |
|---|---|
| `analyze_query` | Classifie la requête (type, stratégie, décomposition nécessaire) |
| `decompose_query` | Décompose les questions complexes en sous-requêtes atomiques |
| `execute_search` | Exécute la recherche avec la stratégie choisie |
| `rerank_results` | Applique un cross-encoder pour un reranking fin |
| `evaluate_quality` | Évalue la suffisance du contexte (score 0.0–1.0) |
| `handle_fallback` | Change de stratégie ou reformule la requête |
| `synthesize_response` | Génère la réponse finale à partir du contexte |

---

## 🔧 Compatibilité descendante

Le système reste **100% rétro-compatible**. Le flag `use_agent` permet de basculer :

```json
// ✅ Mode agent (défaut) — raisonnement dynamique
{ "message": "...", "use_agent": true }

// ✅ Mode statique — pipeline classique
{ "message": "...", "use_agent": false, "use_hybrid": true, "use_hyde": false }
```

---

## 🧪 Tests

### Tests du pipeline

Voir [TEST_README.md](TEST_README.md) pour les tests unitaires du pipeline.

```bash
python test_pipeline.py
```

### Tests API (Postman)

Une collection Postman est disponible avec 5 requêtes de test :

1. **Agent — Requête Simple** → Dense search
2. **Agent — Requête Complexe Multi-Hop** → Décomposition + multi-tool
3. **Agent — Streaming SSE** → Thoughts en temps réel
4. **Statique — Pipeline RAG Classique** → Compatibilité descendante
5. **Sessions — Liste des conversations** → Historique

Collection ID : `185c2487-7b78-4590-94b2-10f5a51b91b7`

---

## 📋 Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `OLLAMA_MODEL_NAME` | Nom du modèle LLM | `mistral-large-3:675b-cloud` |
| `OLLAMA_BASE_URL` | URL de l'API Ollama | `http://ollama:11434` |
| `DEFAULT_TEMPERATURE` | Température de génération | `0.7` |
| `DEFAULT_MAX_TOKENS` | Tokens max de génération | `2048` |
| `QDRANT_HOST` | Hôte Qdrant | `localhost` |
| `QDRANT_PORT` | Port Qdrant | `6333` |
| `QDRANT_COLLECTION_NAME` | Nom de la collection | `seinentai_documents` |
| `MINIO_ENDPOINT` | Endpoint MinIO | `localhost:9000` |
| `MONGODB_URI` | URI MongoDB | `mongodb://root:example@localhost:27017` |
| `MONGODB_DATABASE` | Base MongoDB | `seinentai_db` |

---

## 📦 Dépendances principales

```
fastapi
langgraph>=0.4.0
langchain>=1.2.10
langchain-core>=0.3.0
langchain-ollama>=1.0.1
qdrant-client
pymongo
minio
sentence-transformers
kafka-python
```

---

*Developpé par :*
*Dr EPL*
