import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import minio
from services.minio_service import MinIOService
from text_chunker import TextChunker
from vector_store import VectorStore
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    Gestionnaire de documents pour le système RAG.

    Permet de :
    - Lister les fichiers dans MinIO
    - Indexer tous les documents ou seulement les nouveaux
    - Gérer l'état d'indexation des documents
    """

    def __init__(self, minio_service: MinIOService, vector_store: VectorStore,
                 text_chunker: TextChunker, document_processor: DocumentProcessor,
                 bucket_name: str = "pdf-bucket"):
        """
        Initialise le gestionnaire de documents.

        Args:
            minio_service: Service MinIO pour accéder aux fichiers
            vector_store: Store vectoriel pour l'indexation
            text_chunker: Chunkeur de texte
            document_processor: Processeur de documents
            bucket_name: Nom du bucket MinIO
        """
        self.minio_service = minio_service
        self.vector_store = vector_store
        self.text_chunker = text_chunker
        self.document_processor = document_processor
        self.bucket_name = bucket_name

    def list_minio_files(self) -> List[Dict[str, Any]]:
        """
        Liste tous les fichiers dans le bucket MinIO.

        Returns:
            Liste des fichiers avec métadonnées (nom, taille, date, hash)
        """
        try:
            # Utiliser le service MinIO pour lister les objets
            objects = self.minio_service.list_objects(self.bucket_name)

            files = []
            for obj in objects:
                if obj['filename']:  # Vérifier que ce n'est pas un dossier
                    # Calculer le hash du fichier pour le suivi des changements
                    file_hash = self._calculate_file_hash(obj['filename'])

                    files.append({
                        'filename': obj['filename'],
                        'size': obj['size'],
                        'last_modified': obj['last_modified'],
                        'hash': file_hash,
                        'extension': Path(obj['filename']).suffix.lower()
                    })

            logger.info(f"📁 {len(files)} fichiers trouvés dans le bucket '{self.bucket_name}'")
            return files

        except Exception as e:
            logger.error(f"❌ Erreur listage fichiers MinIO: {e}")
            return []

    def get_indexed_documents(self) -> Set[str]:
        """
        Récupère la liste des documents déjà indexés.

        Returns:
            Ensemble des noms de fichiers indexés
        """
        try:
            # Recherche tous les documents dans Qdrant
            # On utilise une requête vide pour récupérer tous les points
            results = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                limit=10000,  # Ajuster selon le nombre de documents
                with_payload=True
            )

            indexed_files = set()
            for point in results[0]:  # results[0] contient les points
                filename = point.payload.get('filename')
                if filename:
                    indexed_files.add(filename)

            logger.info(f"📊 {len(indexed_files)} documents déjà indexés")
            return indexed_files

        except Exception as e:
            logger.error(f"❌ Erreur récupération documents indexés: {e}")
            return set()

    def get_new_documents(self) -> List[Dict[str, Any]]:
        """
        Identifie les nouveaux documents (présents dans MinIO mais pas indexés).

        Returns:
            Liste des nouveaux documents à indexer
        """
        minio_files = self.list_minio_files()
        indexed_files = self.get_indexed_documents()

        new_documents = []
        for file_info in minio_files:
            if file_info['filename'] not in indexed_files:
                new_documents.append(file_info)

        logger.info(f"🆕 {len(new_documents)} nouveaux documents à indexer")
        return new_documents

    def index_all_documents(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Indexe tous les documents du bucket MinIO.

        Args:
            force_reindex: Si True, réindexe même les documents déjà présents

        Returns:
            Rapport d'indexation
        """
        logger.info("🚀 Démarrage indexation complète des documents")

        minio_files = self.list_minio_files()
        indexed_files = self.get_indexed_documents() if not force_reindex else set()

        report = {
            'total_files': len(minio_files),
            'indexed': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }

        for file_info in minio_files:
            filename = file_info['filename']

            # Vérifier si déjà indexé
            if not force_reindex and filename in indexed_files:
                logger.info(f"⏭️ Déjà indexé: {filename}")
                report['skipped'] += 1
                report['details'].append({
                    'filename': filename,
                    'status': 'skipped',
                    'reason': 'already_indexed'
                })
                continue

            # Traiter et indexer le document
            success = self._index_single_document(filename)
            if success:
                report['indexed'] += 1
                report['details'].append({
                    'filename': filename,
                    'status': 'indexed'
                })
            else:
                report['errors'] += 1
                report['details'].append({
                    'filename': filename,
                    'status': 'error'
                })

        logger.info(f"✅ Indexation terminée: {report['indexed']} indexés, {report['skipped']} ignorés, {report['errors']} erreurs")
        return report

    def index_new_documents(self) -> Dict[str, Any]:
        """
        Indexe seulement les nouveaux documents.

        Returns:
            Rapport d'indexation
        """
        logger.info("🆕 Démarrage indexation des nouveaux documents")

        new_documents = self.get_new_documents()

        report = {
            'total_files': len(new_documents),
            'indexed': 0,
            'errors': 0,
            'details': []
        }

        for file_info in new_documents:
            filename = file_info['filename']

            success = self._index_single_document(filename)
            if success:
                report['indexed'] += 1
                report['details'].append({
                    'filename': filename,
                    'status': 'indexed'
                })
            else:
                report['errors'] += 1
                report['details'].append({
                    'filename': filename,
                    'status': 'error'
                })

        logger.info(f"✅ Indexation nouveaux documents terminée: {report['indexed']} indexés, {report['errors']} erreurs")
        return report

    def _index_single_document(self, filename: str) -> bool:
        """
        Indexe un document individuel.

        Args:
            filename: Nom du fichier dans MinIO

        Returns:
            True si succès
        """
        try:
            logger.info(f"📄 Traitement du document: {filename}")

            # 1. Télécharger le fichier depuis MinIO
            file_content = self._download_from_minio(filename)
            if not file_content:
                return False

            # 2. Traiter le document (extraction du texte)
            text = self.document_processor.process(file_content, filename)
            if not text:
                logger.warning(f"⚠️ Aucun texte extrait de {filename}")
                return False

            # 3. Découper en chunks avec métadonnées
            doc_id = self._generate_doc_id(filename)
            chunks = self.text_chunker.chunk_with_metadata(
                text=text,
                doc_id=doc_id,
                filename=filename,
                metadata={
                    'indexed_at': datetime.now().isoformat(),
                    'file_size': len(file_content),
                    'text_length': len(text)
                }
            )

            # 4. Générer les embeddings (simulation pour l'instant)
            # TODO: Intégrer un vrai modèle d'embeddings
            embeddings = self._generate_embeddings(chunks)

            # 5. Indexer dans le vector store
            success = self.vector_store.index_documents(chunks, embeddings)

            if success:
                logger.info(f"✅ Document indexé: {filename} ({len(chunks)} chunks)")
                return True
            else:
                logger.error(f"❌ Échec indexation: {filename}")
                return False

        except Exception as e:
            logger.error(f"❌ Erreur indexation {filename}: {e}")
            return False

    def _download_from_minio(self, filename: str) -> Optional[bytes]:
        """
        Télécharge un fichier depuis MinIO.

        Args:
            filename: Nom du fichier

        Returns:
            Contenu du fichier en bytes ou None si erreur
        """
        return self.minio_service.get_object(self.bucket_name, filename)

    def _calculate_file_hash(self, filename: str) -> str:
        """
        Calcule le hash d'un fichier pour détecter les changements.

        Args:
            filename: Nom du fichier

        Returns:
            Hash SHA256 du fichier
        """
        try:
            content = self._download_from_minio(filename)
            if content:
                return hashlib.sha256(content).hexdigest()
            return ""
        except Exception:
            return ""

    def _generate_doc_id(self, filename: str) -> str:
        """
        Génère un ID unique pour un document.

        Args:
            filename: Nom du fichier

        Returns:
            ID unique du document
        """
        # Utiliser le hash du nom de fichier pour l'unicité
        return hashlib.md5(filename.encode()).hexdigest()

    def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Any]:
        """
        Génère les embeddings pour les chunks.

        TODO: Intégrer un vrai modèle d'embeddings (sentence-transformers, OpenAI, etc.)

        Args:
            chunks: Liste des chunks

        Returns:
            Liste d'embeddings (pour l'instant des vecteurs aléatoires)
        """
        import numpy as np

        # Simulation d'embeddings - REMPLACER PAR UN VRAI MODÈLE
        vector_size = 384  # Taille standard pour sentence-transformers
        embeddings = []

        for chunk in chunks:
            # Générer un vecteur aléatoire normalisé
            vector = np.random.normal(0, 1, vector_size)
            vector = vector / np.linalg.norm(vector)  # Normalisation
            embeddings.append(vector)

        logger.warning("⚠️ Utilisation d'embeddings aléatoires - À REMPLACER PAR UN VRAI MODÈLE")
        return embeddings

    def get_indexation_status(self) -> Dict[str, Any]:
        """
        Retourne le statut d'indexation global.

        Returns:
            Statistiques d'indexation
        """
        minio_files = self.list_minio_files()
        indexed_files = self.get_indexed_documents()
        new_documents = self.get_new_documents()

        return {
            'total_minio_files': len(minio_files),
            'indexed_files': len(indexed_files),
            'new_files': len(new_documents),
            'indexation_rate': len(indexed_files) / len(minio_files) if minio_files else 0,
            'minio_files': minio_files,
            'new_documents': new_documents
        }