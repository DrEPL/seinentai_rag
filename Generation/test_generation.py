# test_generation.py
import logging
import time
import sys
from typing import Optional

from rag_complete_pipeline import rag_complete_pipeline
from generation import GenerationPipeline
from Retrieval.retrieval_pipeline import RetrieverPipeline

# Configuration logging
logging.basicConfig(level=logging.INFO)

def test_normal_mode(retriever, generator, query: str):
    """Test le mode normal (non-stream)"""
    print("\n" + "="*80)
    print("🔵 TEST MODE NORMAL (NON-STREAM)")
    print("="*80)
    
    start_time = time.time()
    
    result = rag_complete_pipeline(
        query=query,
        retriever_pipeline=retriever,
        generation_pipeline=generator,
        limit=5,
        score_threshold=0.5,
        use_hybrid=True,
    )
    
    elapsed_time = time.time() - start_time
    
    # Afficher les résultats
    if result["success"]:
        print(f"\n📝 QUESTION: {result['query']}")
        print("-"*40)
        print(f"🤖 RÉPONSE:\n{result['response']}")
        print("-"*40)
        print(f"📚 SOURCES ({result['source_stats']['unique_files']} fichiers):")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source['filename']} (score: {source['score']:.2f})")
        print("-"*40)
        print(f"⏱️  Temps total: {elapsed_time:.2f}s")
        print(f"📊 Tokens: {result.get('prompt_tokens', 0)} prompt + {result.get('completion_tokens', 0)} completion")
    else:
        print(f"❌ Erreur: {result.get('error', 'Inconnue')}")
    
    return result

def test_stream_mode(retriever, generator, query: str):
    """Test le mode stream avec affichage en temps réel"""
    print("\n" + "="*80)
    print("🟢 TEST MODE STREAM (AVEC AFFICHAGE TEMPS RÉEL)")
    print("="*80)
    
    # Callback pour le streaming
    def stream_callback(chunk: str):
        """Affiche chaque chunk en temps réel sans retour à la ligne"""
        print(chunk, end='', flush=True)
    
    start_time = time.time()
    first_token_time = None
    
    print(f"\n📝 QUESTION: {query}")
    print("-"*40)
    print("🤖 RÉPONSE (streaming):\n")
    
    # Version streaming du pipeline
    result = generator.generate(
        query=query,
        retrieved_docs=retriever.search(
            query=query,
            limit=10,
            score_threshold=0.5,
            use_hybrid=True
        ),
        stream=True,
        callback=stream_callback
    )
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "-"*40)
    print(f"⏱️  Temps total streaming: {elapsed_time:.2f}s")
    print(f"📊 Tokens: {result.get('prompt_tokens', 0)} prompt + {result.get('completion_tokens', 0)} completion")
    
    return result

def test_stream_with_metadata(retriever, generator, query: str):
    """Test le mode stream avec métadonnées en temps réel"""
    print("\n" + "="*80)
    print("🟣 TEST MODE STREAM AVANCÉ (AVEC MÉTADONNÉES)")
    print("="*80)
    
    class StreamMetrics:
        def __init__(self):
            self.chunks = []
            self.chunk_times = []
            self.start_time = time.time()
            self.first_token_time = None
        
        def callback(self, chunk: str):
            """Callback avec métriques"""
            current_time = time.time()
            
            # Enregistrer le chunk
            self.chunks.append(chunk)
            self.chunk_times.append(current_time)
            
            # Premier token ?
            if self.first_token_time is None:
                self.first_token_time = current_time - self.start_time
                print(f"\n⚡ Premier token après: {self.first_token_time:.3f}s")
                print("-"*40)
            
            # Afficher le chunk
            print(chunk, end='', flush=True)
    
    metrics = StreamMetrics()
    
    # Récupérer les documents d'abord
    print("\n🔍 Récupération des documents...")
    retrieved_docs = retriever.search(
        query=query,
        limit=3,
        score_threshold=0.5,
        use_hybrid=True
    )
    print(f"✅ {len(retrieved_docs)} documents récupérés")
    
    # Lancer le streaming
    print("\n🚀 Démarrage du streaming...")
    result = generator.generate(
        query=query,
        retrieved_docs=retrieved_docs,
        stream=True,
        callback=metrics.callback
    )
    
    # Calculer les métriques
    total_time = time.time() - metrics.start_time
    
    if len(metrics.chunk_times) > 1:
        avg_chunk_time = (metrics.chunk_times[-1] - metrics.chunk_times[0]) / len(metrics.chunks)
    else:
        avg_chunk_time = 0
    
    print("\n" + "-"*40)
    print("📊 MÉTRIQUES DE STREAMING:")
    print(f"  • Temps au premier token: {metrics.first_token_time:.3f}s")
    print(f"  • Nombre de chunks: {len(metrics.chunks)}")
    print(f"  • Temps moyen par chunk: {avg_chunk_time*1000:.2f}ms")
    print(f"  • Débit: {len(result.get('response', '')) / total_time:.1f} chars/s")
    print(f"  • Temps total: {total_time:.2f}s")
    
    return result

def compare_modes(retriever, generator, query: str):
    """Compare les performances des différents modes"""
    print("\n" + "="*80)
    print("📊 COMPARAISON DES MODES")
    print("="*80)
    
    # Test 1: Mode normal
    start_normal = time.time()
    result_normal = rag_complete_pipeline(
        query=query,
        retriever_pipeline=retriever,
        generation_pipeline=generator,
        limit=3,
        score_threshold=0.5,
        use_hybrid=True,
        stream=False
    )
    normal_time = time.time() - start_normal
    
    # Test 2: Mode stream (avec mesure du premier token)
    start_stream = time.time()
    first_token_stream = None
    
    def measure_first_token(chunk):
        nonlocal first_token_stream
        if first_token_stream is None:
            first_token_stream = time.time() - start_stream
    
    result_stream = generator.generate(
        query=query,
        retrieved_docs=retriever.search(query=query, limit=3, score_threshold=0.4, use_hybrid=True),
        stream=True,
        callback=measure_first_token,
        template_name="detailed"
    )
    stream_total = time.time() - start_stream
    
    # Afficher la comparaison
    print("\n" + "-"*40)
    print("🔵 MODE NORMAL:")
    print(f"  • Temps total: {normal_time:.2f}s")
    print(f"  • Tokens: {result_normal.get('completion_tokens', 0)}")
    
    print("\n🟢 MODE STREAM:")
    print(f"  • Temps au premier token: {first_token_stream:.3f}s")
    print(f"  • Temps total: {stream_total:.2f}s")
    print(f"  • Tokens: {result_stream.get('completion_tokens', 0)}")
    
    print("\n📈 GAIN PERÇU PAR L'UTILISATEUR:")
    print(f"  • Premiers mots visibles: {first_token_stream:.3f}s vs attente totale {normal_time:.2f}s")
    print(f"  • Amélioration perception: {((normal_time - first_token_stream) / normal_time * 100):.1f}% plus rapide")
    
    return {
        'normal': {'time': normal_time, 'tokens': result_normal.get('completion_tokens', 0)},
        'stream': {'first_token': first_token_stream, 'total': stream_total, 'tokens': result_stream.get('completion_tokens', 0)}
    }

def test_stream_error_handling(retriever, generator):
    """Test la gestion d'erreurs en mode stream"""
    print("\n" + "="*80)
    print("🟡 TEST GESTION D'ERREURS STREAM")
    print("="*80)
    
    # Test avec requête vide
    print("\n📝 Test 1: Requête vide")
    try:
        result = generator.generate(
            query="",
            retrieved_docs=[],
            stream=True,
            callback=lambda x: None
        )
        print(f"  Résultat: {result.get('success', False)}")
        print(f"  Message: {result.get('error', 'Rien à signaler')}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Test avec callback None
    print("\n📝 Test 2: Callback None")
    try:
        result = generator.generate(
            query="test",
            retrieved_docs=[],
            stream=True,
            callback=None
        )
        print(f"  ✅ Pas d'erreur - géré automatiquement")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Test interruption
    print("\n📝 Test 3: Interruption utilisateur (Ctrl+C simulé)")
    print("  (Appuyez sur Ctrl+C dans les 2 secondes pour tester l'interruption)")
    
    def slow_callback(chunk):
        print(chunk, end='', flush=True)
        time.sleep(0.5)  # Ralentir pour permettre l'interruption
    
    try:
        result = generator.generate(
            query="Test d'interruption. " * 10,
            retrieved_docs=retriever.search(query="test", limit=1),
            stream=True,
            callback=slow_callback
        )
    except KeyboardInterrupt:
        print("\n  ✅ Interruption capturée - streaming arrêté proprement")
    except Exception as e:
        print(f"  Exception: {e}")

def main():
    # Initialiser les pipelines
    print("🚀 Initialisation des pipelines...")
    retriever = RetrieverPipeline()
    generator = GenerationPipeline()
    
    # Vérifier les modèles disponibles
    available_models = generator.list_available_models()
    print(f"📋 Modèles disponibles: {available_models}")
    print(f"🎯 Modèle utilisé: {generator.model_name}")
    
    # Question de test
    query = "C'est quoi la signification de l'uniforme du groupe des jeunes?"
    
    # Menu de test
    print("\n" + "="*80)
    print("🧪 SÉLECTIONNEZ UN TEST:")
    print("="*80)
    print("1. Mode normal uniquement")
    print("2. Mode stream uniquement")
    print("3. Mode stream avec métadonnées")
    print("4. Comparaison normal vs stream")
    print("5. Test gestion d'erreurs")
    print("6. TOUS les tests")
    print("="*80)
    
    # choice = input("\nVotre choix (1-6) [défaut: 4]: ").strip() or "4"
    choice = "2"
    
    if choice == "1":
        test_normal_mode(retriever, generator, query)
    elif choice == "2":
        test_stream_mode(retriever, generator, query)
    elif choice == "3":
        test_stream_with_metadata(retriever, generator, query)
    elif choice == "4":
        compare_modes(retriever, generator, query)
    elif choice == "5":
        test_stream_error_handling(retriever, generator)
    elif choice == "6":
        print("\n🔴 TEST 1: Mode normal")
        test_normal_mode(retriever, generator, query)
        
        print("\n🔴 TEST 2: Mode stream")
        test_stream_mode(retriever, generator, query)
        
        print("\n🔴 TEST 3: Mode stream avancé")
        test_stream_with_metadata(retriever, generator, query)
        
        print("\n🔴 TEST 4: Comparaison")
        compare_modes(retriever, generator, query)
        
        print("\n🔴 TEST 5: Gestion d'erreurs")
        test_stream_error_handling(retriever, generator)
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    # Assurez-vous qu'Ollama tourne avec: ollama serve
    main()