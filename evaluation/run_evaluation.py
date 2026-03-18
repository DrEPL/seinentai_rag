# evaluation/run_evaluation.py
import sys
import os
from Generation.generation import GenerationPipeline
from Ingestion.document_processor import DocumentProcessor
from evaluation.load_test_set import load_robert_test_set
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from Retrieval.retrieval_pipeline import RetrieverPipeline
from evaluation.rag_evaluator import EvaluationOrchestrator
from services.minio_service import MinIOService
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv('../.env')

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_test_questions():
    """Charge les questions de test"""
    return [
        "Qu'est-ce que Robert fais en ville?",
        "Où habite le premier neveu de Robert?",
        "Pourquoi Robert est-il inquiet?",
        "Que regarde le neveu à la télévision?",
        "Comment Robert contacte-t-il ses neveux?",
        "Quelle est la réaction des neveux quand Robert appelle?",
        "Où Robert décide-t-il finalement d'aller?",
        "Que fait Robert avant de partir en ville?",
        "Combien de neveux Robert a-t-il en ville?",
        "Pourquoi Robert ne veut-il pas dormir dehors?"
    ]

def load_ground_truths():
    """Charge les réponses de référence (optionnel)"""
    return [
        "Robert va en ville pour se ravitailler et chercher un logement chez ses neveux.",
        "Le premier neveu habite en ville, mais le texte ne précise pas exactement où.",
        "Robert est inquiet car il craint que ses neveux refusent de l'héberger.",
        "Le neveu regarde un match à la télévision.",
        "Robert utilise son téléphone pour appeler ses neveux.",
        "Les neveux semblent occupés, l'un regarde la télé, l'autre travaille.",
        "Robert décide d'aller à Dakar chez le dernier neveu.",
        "Robert réfléchit à contacter ses neveux et s'inquiète de leur réaction.",
        "Robert a trois neveux en ville.",
        "Robert ne veut pas dormir dehors car il préfère être hébergé par sa famille."
    ]

def main():
    print("="*60)
    print("🔬 ÉVALUATION COMPLÈTE DU PIPELINE RAG")
    print("="*60)
    
    # Initialiser les pipelines
    print("\n🚀 Initialisation des pipelines...")
    retriever = RetrieverPipeline()
    generator = GenerationPipeline()
    
    # Créer l'orchestrateur d'évaluation
    orchestrator = EvaluationOrchestrator(retriever, generator)
    
    # Charger les données de test
    # test_questions = load_test_questions()
    # ground_truths = load_ground_truths()
    
    test_questions, ground_truths, full_set = load_robert_test_set()
    
    # Extraire les documents (pour Giskard)
    # À adapter selon votre source de documents
    minio_client = MinIOService()
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "")
    filename = "NIDJAY ROBERT.pdf"
    documents_pdf = minio_client.get_object(MINIO_BUCKET,filename)
    documents = DocumentProcessor().process(documents_pdf,filename)
    chunk_size = os.getenv("CHUNK_SIZE", 500)
    chunk_overlap=os.getenv('CHUNK_OVERLAP', int(50))
    
    print(f"DEBUG - chunk_size: {chunk_size}, type: {type(chunk_size)}")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,  # Fonction de calcul de longueur (caractères)
        is_separator_regex=False  # Les séparateurs sont des chaînes simples
    )
    doc = Document(page_content=documents)

    # Découpage du document
    langchain_chunks = splitter.split_documents([doc])

    # Conversion en format uniforme avec métadonnées de position
    chunks = []

    for i, chunk_doc in enumerate(langchain_chunks):
        chunk_text = chunk_doc.page_content
        chunks.append(chunk_text)
    
    # Lancer l'évaluation complète
    print("\n📊 Lancement de l'évaluation...")
    results = orchestrator.run_complete_evaluation(
        test_questions=test_questions[:5],
        ground_truths=ground_truths,
        documents=chunks
    )
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("📋 RÉSUMÉ DE L'ÉVALUATION")
    print("="*60)
    
    summary = results["summary"]
    
    print("\n📈 Scores RAGAS:", summary)
    # for metric, score in summary["ragas_scores"].items():
    #     print(f"  - {metric}: {score:.3f}")
    
    # print(f"\n🔒 Sécurité: {summary['overall_assessment']['security']}")
    
    # if "ragas_avg" in summary["overall_assessment"]:
    #     print(f"\n⭐ Note moyenne RAGAS: {summary['overall_assessment']['ragas_avg']}")
    
    print(f"\n✅ Évaluation terminée! Rapports sauvegardés dans /reports")

if __name__ == "__main__":
    main()