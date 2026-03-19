"""
Script de test des composants du pipeline Retriever.

Ce script teste les composants principaux :
- Document Processor
- Text Chunker
- Vector Store
- Pipeline Retriever
"""

import sys
from pathlib import Path
import textwrap

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from retrieval_pipeline import RetrieverPipeline



def test_real_document_processing():
    """Test du traitement d'un vrai document depuis MinIO"""
    print("\n🧪 Test du traitement du document réel...")

    try:
        # Initialisation du pipeline RAG
        pipeline = RetrieverPipeline()

        # Paramètres du document réel
        bucket_name = "pdf-bucket"
        filename = "NIDJAY ROBERT.pdf"

        print(f"🔄 Traitement du document: {bucket_name}/{filename}")

        # Utiliser la vraie fonction process_document
        success = pipeline.process_document(bucket_name, filename)

        if success:
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


def search():
    """Test de recherche sur le document réel"""
    print("\n🧪 Test de recherche sur le document réel...")

    try:
        # Initialisation du pipeline RAG
        pipeline = RetrieverPipeline()

        # Test de recherche avec une requête pertinente
        query = "Où vivre les neveux de Robert ?"
        results = pipeline.search(query, limit=6, score_threshold=0.5, use_hybrid=True)

        if results:
            print(f"✅ Recherche réussie: {len(results)} résultats trouvés")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
                print(f"     \"{result['text']}...\"")
                print(textwrap.fill(f"Resultat N° {i} : {result}" ))
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
    print("🧪 DÉBUT DES TESTS DES COMPOSANTS RAG")
    print("=" * 50)

    results = {}

    # # Tests individuels
    results['document_processing'] = test_real_document_processing()
    # results['real_document_search'] = search()

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