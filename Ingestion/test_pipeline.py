#!/usr/bin/env python3
"""
Script de test des composants du pipeline RAG.

Ce script teste les composants principaux :
- Document Processor
- Text Chunker
- Vector Store
- Pipeline RAG
"""

import logging
import sys
import tempfile
import os
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from text_chunker import TextChunker
from Ingestion.vector_store2 import VectorStore
from document_processor import DocumentProcessor
from Ingestion.ingestion_pipeline import IngestionPipeline



def test_real_document_processing():
    """Test du traitement d'un vrai document depuis MinIO"""
    print("\n🧪 Test du traitement du document réel...")

    try:
        # Initialisation du pipeline RAG
        pipeline = IngestionPipeline()

        # Paramètres du document réel
        bucket_name = "pdf-bucket"
        filename = "NIDJAY ROBERT.pdf"

        print(f"🔄 Traitement du document: {bucket_name}/{filename}")

        # Utiliser la vraie fonction process_document
        embeddings, chunks  = pipeline.process_document(bucket_name, filename)
        
        if embeddings and chunks :
            print(f"✅ Succès! {len(chunks)} chunks traités")
            print(f"   Dimensions embeddings: {len(embeddings[0]) if embeddings else 0}")
            
            # Utilisation des résultats
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                print(f"\nChunk {i+1}:")
                print(f"  Texte: {chunk['text'][:100]}...")
                print(f"  Métadonnées: {chunk['metadata']}")
                print(f"  Embedding shape: {len(embedding)}")
                
                # Stockage dans une base vectorielle
                # vector_store.add(embedding, chunk)
            print(f"✅ Document '{filename}' traité avec succès !")
            return True
        else:
            print(f"❌ Échec du traitement du document '{filename}'")
            return False

    except Exception as e:
        print(f"❌ Erreur lors du traitement du document réel: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_document_search():
    """Test de recherche sur le document réel"""
    print("\n🧪 Test de recherche sur le document réel...")

    try:
        # Initialisation du pipeline RAG
        pipeline = IngestionPipeline()

        # Test de recherche avec une requête pertinente
        query = "Qui est l'oncle robert ?"
        results = pipeline.search(query, limit=6)

        if results:
            print(f"✅ Recherche réussie: {len(results)} résultats trouvés")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
                print(f"     \"{result['text']}...\"")
            return True
        else:
            print("❌ Aucun résultat de recherche trouvé")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale de test"""
    print("🧪 DÉBUT DES TESTS DU PIPELINE INGESTION")
    print("=" * 50)

    results = {}

    # # Tests individuels
    results['document_processing'] = test_real_document_processing()
    # results['real_document_search'] = test_real_document_search()

    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS DES TESTS")

    passed = 0
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if success:
            passed += 1

    print(f"\n📈 Score: {passed}/{total} tests réussis")

    if passed == total:
        print("🎉 Tous les tests sont passés ! Les composants RAG fonctionnent.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les logs ci-dessus.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)