# test_generation.py
import logging

from rag_complete_pipeline import rag_complete_pipeline
from generation import GenerationPipeline
from Retrieval.retrieval_pipeline import RetrieverPipeline

# Configuration logging
logging.basicConfig(level=logging.INFO)

def main():
    # 1. Initialiser les pipelines
    retriever = RetrieverPipeline()
    
    generator = GenerationPipeline()
    
    # 2. Optionnel: Vérifier les modèles disponibles
    available_models = generator.list_available_models()
    print(f"Modèles disponibles: {available_models}")
    
    # 3. Exécuter le pipeline complet
    query = "Qu'est-ce que Robert fait en ville? "
    
    result = rag_complete_pipeline(
        query=query,
        retriever_pipeline=retriever,
        generation_pipeline=generator,
        limit=3,
        score_threshold=0.3,
        use_hybrid=True,
        template_name="detailed"
    )
    
    # 4. Afficher les résultats
    if result["success"]:
        print("\n" + "="*80)
        print(f"📝 QUESTION: {result['query']}")
        print("="*80)
        print(f"\n🤖 RÉPONSE:\n{result['response']}")
        print("\n" + "="*80)
        print(f"📚 SOURES ({result['source_stats']['unique_files']} fichiers uniques):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n  {i}. {source['filename']} (score: {source['score']:.2f})")
            print(f"     Extrait: {source['text'][:100]}...")
        print("="*80)
        print(f"\n⏱️  Temps génération: {result['generation_time']:.2f}s")
        print(f"📊 Tokens: {result.get('prompt_tokens', 0)} prompt + {result.get('completion_tokens', 0)} completion")
    else:
        print(f"❌ Erreur: {result.get('error', 'Inconnue')}")

if __name__ == "__main__":
    # Assurez-vous qu'Ollama tourne avec: ollama serve
    main()