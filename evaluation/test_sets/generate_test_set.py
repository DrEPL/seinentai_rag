# evaluation/test_sets/generate_test_set.py
import json
from typing import List
from datasets import Dataset
from evaluation.metrics_config import OllamaRagasLLM, SentenceEmbeddings

class TestSetGenerator:
    """Génère des jeux de test pour l'évaluation"""
    
    def __init__(self):
        self.ragas_llm = OllamaRagasLLM().get_ragas_llm()
        self.embeddings = SentenceEmbeddings().get_ragas_embeddings()
        
    def generate_from_documents(self, documents: List[str], num_questions: int = 20) -> Dataset:
        """
        Génère un jeu de test à partir de documents
        
        Args:
            documents: Liste de textes
            num_questions: Nombre de questions à générer
            
        Returns:
            Dataset avec questions/réponses de référence
        """
        from ragas.testset import TestsetGenerator
        
        generator = TestsetGenerator(
            llm=self.ragas_llm,
            embedding_model=self.embeddings
        )
        
        testset = generator.generate(
            query_distribution=documents,
            testset_size=num_questions
        )
        
        return testset
    
    def create_manual_testset(self, questions_file: str = "questions.json") -> Dataset:
        """
        Crée un jeu de test manuel à partir d'un fichier JSON
        
        Format du fichier:
        [
            {
                "question": "...",
                "ground_truth": "...",
                "contexts": ["...", "..."],
                "metadata": {...}
            }
        ]
        """
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Dataset.from_list(data)
    
    def save_testset(self, testset: Dataset, filename: str):
        """Sauvegarde le jeu de test"""
        testset.to_pandas().to_json(filename, orient='records', indent=2)
        print(f"✅ Testset sauvegardé: {filename}")