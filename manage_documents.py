#!/usr/bin/env python3
"""
Script de gestion des documents pour le système RAG.

Permet de :
- Lister les fichiers dans MinIO
- Indexer tous les documents
- Indexer seulement les nouveaux documents
- Voir le statut d'indexation
"""

import logging
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from services.minio_service import MinIOService
from text_chunker import TextChunker
from vector_store import VectorStore
from document_processor import DocumentProcessor
from document_manager import DocumentManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_menu():
    """Affiche le menu principal"""
    print("\n" + "="*60)
    print("📚 GESTIONNAIRE DE DOCUMENTS RAG")
    print("="*60)
    print("1. 📁 Lister les fichiers MinIO")
    print("2. 📊 Voir le statut d'indexation")
    print("3. 🆕 Indexer les nouveaux documents")
    print("4. 🔄 Réindexer tous les documents")
    print("5. 🗑️  Supprimer l'indexation d'un document")
    print("6. 🔍 Tester la recherche")
    print("0. ❌ Quitter")
    print("="*60)


def list_minio_files(manager: DocumentManager):
    """Liste les fichiers dans MinIO"""
    print("\n📁 Fichiers dans MinIO:")
    files = manager.list_minio_files()

    if not files:
        print("❌ Aucun fichier trouvé")
        return

    for i, file_info in enumerate(files, 1):
        size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] else 0
        print(f"{i:2d}. {file_info['filename']} ({size_mb:.1f} MB) - {file_info['extension']}")


def show_indexation_status(manager: DocumentManager):
    """Affiche le statut d'indexation"""
    print("\n📊 Statut d'indexation:")
    status = manager.get_indexation_status()

    print(f"📁 Fichiers dans MinIO: {status['total_minio_files']}")
    print(f"📊 Documents indexés: {status['indexed_files']}")
    print(f"🆕 Nouveaux documents: {status['new_files']}")
    print(".1%")

    if status['new_documents']:
        print("\n🆕 Nouveaux documents à indexer:")
        for doc in status['new_documents'][:5]:  # Afficher les 5 premiers
            print(f"  - {doc['filename']}")
        if len(status['new_documents']) > 5:
            print(f"  ... et {len(status['new_documents']) - 5} autres")


def index_new_documents(manager: DocumentManager):
    """Indexe les nouveaux documents"""
    print("\n🆕 Indexation des nouveaux documents...")

    confirm = input("Continuer ? (o/N): ")
    if confirm.lower() != 'o':
        print("❌ Annulé")
        return

    report = manager.index_new_documents()

    print("✅ Rapport d'indexation:")
    print(f"📄 Documents traités: {report['total_files']}")
    print(f"✅ Indexés: {report['indexed']}")
    print(f"❌ Erreurs: {report['errors']}")

    if report['errors'] > 0:
        print("\n❌ Documents en erreur:")
        for detail in report['details']:
            if detail['status'] == 'error':
                print(f"  - {detail['filename']}")


def reindex_all_documents(manager: DocumentManager):
    """Réindexe tous les documents"""
    print("\n🔄 Réindexation complète de tous les documents...")
    print("⚠️  ATTENTION: Cela va supprimer et recréer tout l'index!")

    confirm = input("Êtes-vous sûr ? Cette action est irréversible ! (oui/NON): ")
    if confirm.lower() != 'oui':
        print("❌ Annulé")
        return

    report = manager.index_all_documents(force_reindex=True)

    print("✅ Rapport de réindexation:")
    print(f"📄 Documents traités: {report['total_files']}")
    print(f"✅ Réindexés: {report['indexed']}")
    print(f"⏭️ Ignorés: {report['skipped']}")
    print(f"❌ Erreurs: {report['errors']}")


def delete_document_indexation(manager: DocumentManager):
    """Supprime l'indexation d'un document"""
    print("\n🗑️ Suppression d'indexation:")

    doc_id = input("Entrez l'ID du document à supprimer: ").strip()
    if not doc_id:
        print("❌ ID vide")
        return

    confirm = input(f"Supprimer l'indexation du document '{doc_id}' ? (o/N): ")
    if confirm.lower() != 'o':
        print("❌ Annulé")
        return

    success = manager.vector_store.delete_document(doc_id)
    if success:
        print(f"✅ Document '{doc_id}' supprimé de l'index")
    else:
        print(f"❌ Erreur suppression document '{doc_id}'")


def test_search(manager: DocumentManager):
    """Test de recherche dans l'index"""
    print("\n🔍 Test de recherche:")

    query = input("Entrez votre requête: ").strip()
    if not query:
        print("❌ Requête vide")
        return

    # TODO: Générer l'embedding de la requête
    # Pour l'instant, on utilise un vecteur aléatoire
    import numpy as np
    query_embedding = np.random.normal(0, 1, 384)
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    results = manager.vector_store.search(query_embedding, limit=3)

    if not results:
        print("❌ Aucun résultat trouvé")
        return

    print(f"\n📋 Résultats pour '{query}':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 📄 {result['filename']} (score: {result['score']:.3f})")
        print(f"   📝 {result['text'][:200]}...")


def main():
    """Fonction principale"""
    print("🚀 Initialisation du gestionnaire de documents...")

    try:
        # Initialisation des services
        minio_service = MinIOService()
        minio_service.setup(bucket_name="pdf-bucket")

        vector_store = VectorStore()
        vector_store.create_collection(vector_size=384)

        text_chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        document_processor = DocumentProcessor()

        # Création du gestionnaire
        manager = DocumentManager(
            minio_service=minio_service,
            vector_store=vector_store,
            text_chunker=text_chunker,
            document_processor=document_processor
        )

        print("✅ Services initialisés avec succès")

        # Boucle principale
        while True:
            print_menu()
            choice = input("\nVotre choix: ").strip()

            if choice == '0':
                print("👋 Au revoir!")
                break
            elif choice == '1':
                list_minio_files(manager)
            elif choice == '2':
                show_indexation_status(manager)
            elif choice == '3':
                index_new_documents(manager)
            elif choice == '4':
                reindex_all_documents(manager)
            elif choice == '5':
                delete_document_indexation(manager)
            elif choice == '6':
                test_search(manager)
            else:
                print("❌ Choix invalide")

            input("\nAppuyez sur Entrée pour continuer...")

    except Exception as e:
        logger.error(f"❌ Erreur initialisation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()