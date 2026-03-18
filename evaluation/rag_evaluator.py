# evaluation/rag_evaluator.py
import logging
import os
from typing import List, Dict, Optional
from datasets import Dataset
from datetime import datetime
import json

import pandas as pd
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_relevancy,
    answer_correctness,
    # answer_accuracy,
    answer_similarity
    # _semantic_similarity
)

from evaluation.deepeval_evaluator import DeepEvalEvaluator
from evaluation.giskard_scanner import GiskardScanner
from evaluation.metrics_config import OllamaRagasLLM, SentenceEmbeddings

logger = logging.getLogger(__name__)

class RAGEvaluator:
    """Évaluateur RAG basé sur RAGAS"""
    
    def __init__(self):
        """
        Initialise l'évaluateur RAGAS
        """
        self.llm_wrapper = OllamaRagasLLM().get_ragas_llm()
        self.embeddings_wrapper = SentenceEmbeddings().get_ragas_embeddings()
        
        # Configuration des métriques
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_relevancy,
            answer_correctness,
            answer_similarity,
            # answer_accuracy,
            # _semantic_similarity
        ]
        
        # Initialiser les métriques avec le LLM
        for metric in self.metrics:
            metric.__setattr__("llm", self.llm_wrapper)
            if hasattr(metric, "embeddings"):
                metric.__setattr__("embeddings", self.embeddings_wrapper)
    
    def prepare_dataset(self, 
                       questions: List[str],
                       answers: List[str],
                       contexts: List[List[str]],
                       ground_truths: Optional[List[str]] = None) -> Dataset:
        """
        Prépare un dataset pour l'évaluation
        
        Args:
            questions: Liste des questions
            answers: Réponses générées par le LLM
            contexts: Contextes récupérés par le retriever
            ground_truths: Réponses de référence (optionnel)
        """
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts
        }
        
        if ground_truths:
            data["ground_truth"] = ground_truths
            
        return Dataset.from_dict(data)
    
    def evaluate(self, 
                dataset: Dataset,
                metrics: Optional[List] = None) -> Dict[str, float]:
        """
        Évalue les performances RAG
        
        Args:
            dataset: Dataset préparé
            metrics: Liste des métriques à calculer
            
        Returns:
            Dictionnaire des scores
        """
        from ragas import evaluate
        
        logger.info(f"🚀 Démarrage évaluation RAGAS avec {OllamaRagasLLM().model_name}")
        
        # Utiliser les métriques spécifiées ou toutes
        metrics_to_use = metrics or self.metrics
        
        # Exécuter l'évaluation
        result = evaluate(
            dataset=dataset,
            metrics=metrics_to_use,
            llm=self.llm_wrapper,
            embeddings=self.embeddings_wrapper,
            batch_size=3
        )
        
        # Convertir en dict
        scores = {}
        for metric in metrics_to_use:
            metric_name = metric.name if hasattr(metric, 'name') else str(metric)
            scores[metric_name] = result[metric_name]
        
        logger.info(f"✅ Évaluation terminée: {scores}")
        return scores
    
    def evaluate_pipeline(self,
                         retriever_pipeline,
                         generation_pipeline,
                         test_questions: List[str],
                         ground_truths: Optional[List[str]] = None,
                         k: int = 3) -> Dict:
        """
        Évalue le pipeline RAG complet
        
        Args:
            retriever_pipeline: Pipeline de retrieval
            generation_pipeline: Pipeline de génération
            test_questions: Questions de test
            ground_truths: Réponses de référence
            k: Nombre de documents à récupérer
        """
        answers = []
        contexts = []
        
        # Exécuter le pipeline pour chaque question
        for i, question in enumerate(test_questions):
            logger.info(f"Traitement question {i+1}/{len(test_questions)}")
            
            # Retrieval
            retrieved = retriever_pipeline.search(
                query=question,
                limit=k,
                use_hybrid=True
            )
            
            # Extraire les contextes
            doc_contexts = [doc.get('text', '') for doc in retrieved]
            contexts.append(doc_contexts)
            
            # Génération
            response = generation_pipeline.generate(
                query=question,
                retrieved_docs=retrieved
            )
            
            answers.append(response['response'] if response['success'] else "")
        
        # Préparer le dataset
        dataset = self.prepare_dataset(
            questions=test_questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths
        )
        
        # Évaluer
        scores = self.evaluate(dataset)
        
        return {
            "scores": scores,
            "details": {
                "questions": test_questions,
                "answers": answers,
                "contexts": contexts
            },
            "timestamp": datetime.now().isoformat(),
            "model": OllamaRagasLLM().model_name
        }
    
    def save_report(self, results: Dict, filename: str = "ragas_report.json"):
        """Sauvegarde le rapport d'évaluation avec création du dossier"""
        
        # Créer le dossier reports s'il n'existe pas
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            logger.info(f"📁 Dossier '{reports_dir}' créé")
        
        # Sauvegarder le fichier
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"📊 Rapport sauvegardé: {filepath}")
        
        
# evaluation/rag_evaluator.py (suite)
class EvaluationOrchestrator:
    """Orchestrateur pour toutes les évaluations"""
    
    def __init__(self, retriever_pipeline, generation_pipeline):
        self.retriever = retriever_pipeline
        self.generator = generation_pipeline
        
        # Initialiser les évaluateurs
        # self.ragas_evaluator = RAGEvaluator()
        # self.deepeval_evaluator = DeepEvalEvaluator()
        self.giskard_scanner = GiskardScanner()
        
    def run_complete_evaluation(self, 
                               test_questions: List[str],
                               ground_truths: Optional[List[str]] = None,
                               documents: Optional[List[str]] = None) -> Dict:
        """
        Lance une évaluation complète avec tous les outils
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "model": self.generator.model_name,
            "ragas": {},
            "deepeval": {},
            "giskard": {}
        }
        
        # 1. Évaluation RAGAS
        logger.info("="*50)
        logger.info("📊 Étape 1: Évaluation RAGAS")
        print("📊 Étape 1: Évaluation RAGAS")
        logger.info("="*50)
        
        # ragas_results = self.ragas_evaluator.evaluate_pipeline(
        #     self.retriever,
        #     self.generator,
        #     test_questions,
        #     ground_truths
        # )
        # results["ragas"] = ragas_results
        # self.ragas_evaluator.save_report(ragas_results, "ragas_results.json")
        
        # 2. Évaluation DeepEval
        logger.info("="*50)
        logger.info("📊 Étape 2: Évaluation DeepEval")
        print("📊 Étape 2: Évaluation DeepEval")
        logger.info("="*50)
        
        # deepeval_results = self.deepeval_evaluator.evaluate_pipeline(
        #     self.retriever,
        #     self.generator,
        #     test_questions,
        #     ground_truths
        # )
        # results["deepeval"] = deepeval_results
        
        # 3. Scan Giskard (si documents fournis)
        if documents:
            logger.info("="*50)
            logger.info("🔒 Étape 3: Scan Giskard")
            print("🔒 Étape 3: Scan Giskard")
            logger.info("="*50)
            
            # Créer la fonction de prédiction
            def predict_fn(df: pd.DataFrame) -> List[str]:
                responses = []
                for question in df["question"]:
                    retrieved = self.retriever.search(question, limit=3)
                    response = self.generator.generate(question, retrieved)
                    responses.append(response['response'] if response['success'] else "")
                return responses
            
            # Créer le modèle Giskard
            giskard_model = self.giskard_scanner.create_giskard_model(predict_fn)
            
            # Scanner les vulnérabilités
            vuln_results = self.giskard_scanner.scan_vulnerabilities(
                giskard_model,
                test_questions[:10]  # Sous-ensemble pour le scan
            )
            results["giskard"]["vulnerabilities"] = vuln_results
            
            # Évaluer le RAG avec Giskard
            knowledge_base = self.giskard_scanner.create_knowledge_base(documents)
            rag_report = self.giskard_scanner.evaluate_rag(
                lambda q: self.generator.generate(q, self.retriever.search(q, limit=3))['response'],
                knowledge_base,
                num_questions=20
            )
            results["giskard"]["rag_report"] = {
                "metrics": rag_report.metrics if hasattr(rag_report, 'metrics') else {}
            }
        
        # Résumé
        results["summary"] = self._generate_summary(results)
        
        # Sauvegarder tout
        self._save_full_report(results)
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Génère un résumé des résultats"""
        summary = {
            "ragas_scores": results["ragas"]["scores"],
            "deepeval_metrics": results["deepeval"].get("scores", {}),
            "giskard_issues": results["giskard"].get("vulnerabilities", {}).get("vulnerabilities", {}),
            "overall_assessment": {}
        }
        
        # Calculer une note moyenne RAGAS
        if summary["ragas_scores"]:
            avg_score = sum(summary["ragas_scores"].values()) / len(summary["ragas_scores"])
            summary["overall_assessment"]["ragas_avg"] = round(avg_score, 3)
        
        # Évaluation qualitative
        if summary.get("giskard_issues", {}).get("total_issues", 0) > 5:
            summary["overall_assessment"]["security"] = "⚠️ Attention: nombreuses vulnérabilités"
        else:
            summary["overall_assessment"]["security"] = "✅ Bon niveau de sécurité"
        
        return summary
    
    def _save_full_report(self, results: Dict):
        """Sauvegarde le rapport complet"""
        filename = f"reports/full_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📊 Rapport complet sauvegardé: {filename}")