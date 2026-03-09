Document source
      │
      ▼
Parsing
      │
      ▼
Chunking
      │
      ▼
Embeddings
      │
      ▼
Indexation vectorielle

# Gestionnaire de Documents RAG

Ce système permet de gérer l'indexation automatique des documents stockés dans MinIO pour un système RAG (Retrieval-Augmented Generation).

## Architecture

```
MinIO Bucket ── DocumentManager ── TextChunker ── VectorStore (Qdrant)
     │                │                 │               │
     └─ Fichiers      └─ Gestion        └─ Chunking    └─ Indexation
        PDF/DOCX         indexation         texte          vectorielle
```

## Composants

### DocumentManager
- **Rôle**: Orchestre l'indexation des documents
- **Fonctionnalités**:
  - Liste les fichiers dans MinIO
  - Détecte les nouveaux documents
  - Indexe automatiquement les documents
  - Gère l'état d'indexation

### DocumentProcessor
- **Rôle**: Extrait le texte des différents formats de documents
- **Formats supportés**: PDF, DOCX, Markdown, TXT, CSV, JSON

### TextChunker
- **Rôle**: Découpe le texte en chunks avec chevauchement
- **Utilise**: LangChain pour un découpage intelligent
- **Méthodes**: récursif, par caractères, par phrases, par paragraphes

### VectorStore
- **Rôle**: Stockage et recherche vectorielle
- **Backend**: Qdrant
- **Fonctionnalités**: indexation, recherche sémantique, suppression

## Utilisation

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Le système utilise les services suivants (via Docker Compose):
- **MinIO**: Stockage objet (port 9000)
- **Qdrant**: Base de données vectorielle (port 6333)
- **Kafka**: Messagerie (optionnel pour les notifications)

### Lancement

```bash
# Démarrer les services
docker-compose up -d

# Lancer le gestionnaire de documents
python manage_documents.py
```

## Interface Utilisateur

Le script `manage_documents.py` fournit une interface en ligne de commande avec les options suivantes:

1. **📁 Lister les fichiers MinIO**
   - Affiche tous les fichiers présents dans le bucket

2. **📊 Voir le statut d'indexation**
   - Nombre total de fichiers
   - Documents déjà indexés
   - Nouveaux documents à indexer

3. **🆕 Indexer les nouveaux documents**
   - Détecte automatiquement les fichiers non indexés
   - Les traite et les ajoute à l'index vectoriel

4. **🔄 Réindexer tous les documents**
   - Supprime et recréé complètement l'index
   - ATTENTION: opération destructive

5. **🗑️ Supprimer l'indexation d'un document**
   - Supprime un document spécifique de l'index

6. **🔍 Tester la recherche**
   - Effectue une recherche sémantique dans l'index

## Workflow d'Indexation

### Indexation Automatique

```python
from document_manager import DocumentManager

# Initialisation
manager = DocumentManager(...)

# Indexer seulement les nouveaux documents
report = manager.index_new_documents()

# Ou réindexer tout
report = manager.index_all_documents(force_reindex=True)
```

### Indexation Manuelle

```python
# Traiter un document spécifique
text = document_processor.process(file_content, filename)
chunks = text_chunker.chunk_with_metadata(text, doc_id, filename)
embeddings = generate_embeddings(chunks)  # À implémenter
vector_store.index_documents(chunks, embeddings)
```

## Formats de Données

### Chunk Format

Chaque chunk contient:

```python
{
    'text': str,           # Contenu du chunk
    'start_char': int,     # Position début dans le texte original
    'end_char': int,       # Position fin dans le texte original
    'chunk_index': int,    # Index du chunk (0, 1, 2, ...)
    'total_chunks': int,   # Nombre total de chunks
    'doc_id': str,         # ID unique du document
    'filename': str,       # Nom du fichier source
    'metadata': dict       # Métadonnées supplémentaires
}
```

### Métadonnées

Les métadonnées incluent:
- Configuration du chunkeur
- Date d'indexation
- Taille du fichier
- Longueur du texte extrait

## Extensions Possibles

### 1. Intégration d'Embeddings Réels

Remplacer la génération aléatoire d'embeddings:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([chunk['text'] for chunk in chunks])
```

### 2. Interface Web

Ajouter une interface web avec Flask/Django pour une gestion plus conviviale.

### 3. Surveillance Continue

Utiliser les notifications Kafka de MinIO pour indexer automatiquement les nouveaux fichiers.

### 4. Métriques et Monitoring

Ajouter des métriques Prometheus pour surveiller les performances d'indexation.

## Dépannage

### Problèmes Courants

1. **Connexion MinIO refusée**
   - Vérifier que le conteneur MinIO est démarré
   - Vérifier les credentials dans `MinIOService`

2. **Erreur d'indexation Qdrant**
   - Vérifier que la collection existe
   - Vérifier la taille des vecteurs (384 par défaut)

3. **Documents non extraits**
   - Vérifier le format du fichier
   - Vérifier les logs du `DocumentProcessor`

### Logs

Les logs sont configurés pour afficher:
- Informations d'indexation
- Erreurs de traitement
- Statistiques de performance

## API Reference

### DocumentManager

- `list_minio_files()`: Liste les fichiers MinIO
- `get_indexed_documents()`: Documents déjà indexés
- `get_new_documents()`: Nouveaux documents à indexer
- `index_new_documents()`: Indexe les nouveaux documents
- `index_all_documents()`: Indexe tous les documents

### TextChunker

- `chunk_text()`: Découpe en chunks basiques
- `chunk_with_metadata()`: Découpe avec métadonnées complètes

### VectorStore

- `index_documents()`: Indexe des chunks
- `search()`: Recherche sémantique
- `delete_document()`: Supprime un document

---

Ce système fournit une base solide pour l'indexation automatique de documents dans un système RAG, avec possibilité d'extension et d'intégration dans des pipelines plus complexes.