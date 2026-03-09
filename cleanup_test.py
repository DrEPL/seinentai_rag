#!/usr/bin/env python3
"""
Script de nettoyage des données de test.

Supprime :
- Les documents de test dans MinIO
- Les index correspondants dans Qdrant
"""

import logging
import sys
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from minio_service import MinIOService
from vector_store import VectorStore


def cleanup_test_data():
    """Nettoie les données de test"""
    print("🧹 Nettoyage des données de test...")

    # Documents de test créés par test_pipeline.py
    test_files = [
        "intelligence_artificielle.txt",
        "guide_python.txt",
        "bioinformatique.txt"
    ]

    try:
        # Nettoyer MinIO
        minio_service = MinIOService()
        minio_service.setup(bucket_name="pdf-bucket")

        print("🗑️ Suppression des fichiers de test dans MinIO...")
        for filename in test_files:
            try:
                minio_service.client.remove_object("pdf-bucket", filename)
                print(f"✅ Supprimé de MinIO: {filename}")
            except Exception as e:
                print(f"⚠️ Non trouvé dans MinIO: {filename} ({e})")

        # Nettoyer Qdrant
        vector_store = VectorStore()

        print("🗑️ Suppression des index de test dans Qdrant...")
        for filename in test_files:
            # Générer le même doc_id que dans DocumentManager
            doc_id = filename.replace('.', '_').replace(' ', '_')
            success = vector_store.delete_document(doc_id)
            if success:
                print(f"✅ Supprimé de Qdrant: {doc_id}")
            else:
                print(f"⚠️ Non trouvé dans Qdrant: {doc_id}")

        print("✅ Nettoyage terminé !")

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

    return True


def reset_collections():
    """Remet à zéro les collections (option destructive)"""
    print("⚠️ Remise à zéro des collections...")

    confirm = input("ATTENTION: Cela va supprimer TOUTES les données indexées ! Continuer ? (oui/NON): ")
    if confirm.lower() != 'oui':
        print("❌ Annulé")
        return

    try:
        vector_store = VectorStore()

        # Supprimer et recréer la collection
        collection_name = vector_store.collection_name

        # Supprimer la collection existante
        try:
            vector_store.client.delete_collection(collection_name)
            print(f"✅ Collection supprimée: {collection_name}")
        except Exception:
            print(f"⚠️ Collection non trouvée: {collection_name}")

        # Recréer la collection
        vector_store.create_collection(vector_size=384)
        print(f"✅ Collection recréée: {collection_name}")

    except Exception as e:
        print(f"❌ Erreur remise à zéro: {e}")


def main():
    """Fonction principale"""
    print("🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("=" * 40)

    # Nettoyage des données de test
    cleanup_test_data()

    # Option de remise à zéro complète
    print("\n" + "=" * 40)
    reset = input("Voulez-vous aussi remettre à zéro les collections ? (o/N): ")
    if reset.lower() == 'o':
        reset_collections()

    print("\n✅ Nettoyage terminé !")


if __name__ == "__main__":
    main()