# evaluation/giskard_scanner.py
import logging
import os
from dotenv import load_dotenv
import pandas as pd
from typing import Callable, List, Dict
import giskard
from giskard import Model, scan, Dataset as GiskardDataset
from giskard.rag import KnowledgeBase, generate_testset, evaluate, RAGReport

logger = logging.getLogger(__name__)

load_dotenv('../.env')

import os
# Forcer l'utilisation d'Ollama
os.environ["OPENAI_API_KEY"] = "sk-dummy"  # Dummy key
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"  # Ollama compatible OpenAI

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
DEEP_EVAL_MODEL_NAME = os.getenv('DEEP_EVAL_MODEL_NAME', '')

class GiskardScanner:
    """Scanner de sécurité et qualité avec Giskard"""
    
    def __init__(self):
        """
        Initialise le scanner Giskard
        
        Args:
            model_name: Modèle à scanner
        """
        self.model_name = DEEP_EVAL_MODEL_NAME
        
        # Configurer Giskard pour utiliser Ollama
        giskard.llm.set_llm_model(
            f"ollama/{self.model_name}",
            api_base=OLLAMA_BASE_URL
        )
        # giskard.llm.set_embedding_model(
        #     "ollama/nomic-embed-text:v1.5",  # ou votre modèle d'embeddings
        #     api_base=OLLAMA_BASE_URL
        # )
        pass
    
    def create_giskard_model(self, 
                            predict_fn: Callable,
                            model_type: str = "text_generation") -> Model:
        """
        Crée un modèle Giskard
        
        Args:
            predict_fn: Fonction de prédiction
            model_type: Type de modèle
        """
        return Model(
            model=predict_fn,
            model_type=model_type,
            name=f"RAG Pipeline - {self.model_name}",
            description="Pipeline RAG complet",
            feature_names=["question"]
        )
    
    def scan_vulnerabilities(self, 
                            model: Model,
                            sample_questions: List[str]) -> Dict:
        """
        Scanne les vulnérabilités du modèle
        
        Args:
            model: Modèle Giskard
            sample_questions: Questions d'exemple
            
        Returns:
            Rapport de vulnérabilités
        """
        logger.info("🔍 Scan des vulnérabilités avec Giskard...")
        
        # Créer un dataset de test
        df = pd.DataFrame({"question": sample_questions})
        giskard_dataset = GiskardDataset(df, target=None)
        
        # Lancer le scan
        scan_results = scan(model, giskard_dataset)
        
        # Générer le rapport
        html_report = scan_results.to_html()
        
        # Sauvegarder
        try:
            os.makedirs("reports", exist_ok=True)
            with open("reports/giskard_scan.html", "w", encoding="utf-8") as f:
                f.write(html_report)
        except IOError as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
        
        # Extraire les vulnérabilités
        # Giskard utilise .issues et .category
        issues = scan_results.issues
        vulnerabilities = {
            "prompt_injection": len([i for i in issues if i.category == "Prompt Injection"]),
            "harmful_content": len([i for i in issues if i.category == "Harmful Content"]),
            "stereotypes": len([i for i in issues if i.category == "Stereotypes"]),
            "hallucination": len([i for i in issues if i.category == "Hallucination"]),
            "total_issues": len(scan_results.issues)
        }
        
        logger.info(f"✅ Scan terminé: {vulnerabilities['total_issues']} problèmes trouvés")
        
        return {
            "vulnerabilities": vulnerabilities,
            "report_path": "reports/giskard_scan.html"
        }
    
    def create_knowledge_base(self, documents: List[str]) -> KnowledgeBase:
        """
        Crée une base de connaissances pour l'évaluation RAG
        
        Args:
            documents: Liste de documents
        """
        df = pd.DataFrame(documents, columns=["text"])
        return KnowledgeBase(df)
    
    def evaluate_rag(self,
                    answer_fn: Callable,
                    knowledge_base: KnowledgeBase,
                    num_questions: int = 50) -> RAGReport:
        """
        Évalue un système RAG
        
        Args:
            answer_fn: Fonction qui prend une question et retourne une réponse
            knowledge_base: Base de connaissances
            num_questions: Nombre de questions à générer
        """
        from giskard.rag import generate_testset
        from giskard.rag.metrics.ragas_metrics import (
            ragas_context_recall,
            ragas_context_precision
        )
        
        # Générer le jeu de test
        testset = generate_testset(
            knowledge_base,
            num_questions=num_questions,
            agent_description="Assistant répondant à des questions sur les documents",
            language="fr"
        )
        
        # Évaluer
        rag_report = evaluate(
            answer_fn,
            testset=testset,
            knowledge_base=knowledge_base,
            metrics=[ragas_context_recall, ragas_context_precision]
        )
        
        # Sauvegarder
        rag_report.save("reports/giskard_rag_report")
        
        return rag_report