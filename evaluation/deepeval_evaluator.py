# evaluation/deepeval_evaluator.py
import logging
from typing import List, Dict, Any, Optional
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    BiasMetric,
    ToxicityMetric
)

from .metrics_config import OllamaDeepEvalModel

logger = logging.getLogger(__name__)

class DeepEvalEvaluator:
    """Évaluateur avec DeepEval"""
    
    def __init__(self):
        """
        Initialise l'évaluateur DeepEval
        
        """
        self.ollama_model = OllamaDeepEvalModel()
        
        # Initialiser les métriques
        self.metrics = {
            # "answer_relevancy": AnswerRelevancyMetric(
            #     threshold=0.5,
            #     model=self.ollama_model,
            #     async_mode=False
            # ),
            # "faithfulness": FaithfulnessMetric(
            #     threshold=0.5,
            #     model=self.ollama_model,
            #     async_mode=False
            # ),
            # "contextual_precision": ContextualPrecisionMetric(
            #     threshold=0.5,
            #     model=self.ollama_model,
            #     async_mode=False      
            # ),
            "contextual_recall": ContextualRecallMetric(
                threshold=0.5,
                model=self.ollama_model,
                async_mode=False
            ),
            "bias": BiasMetric(
                threshold=0.5,
                model=self.ollama_model,
                async_mode=False
            ),
            "toxicity": ToxicityMetric(
                threshold=0.5,
                model=self.ollama_model,
                async_mode=False
            )
        }
    
    def create_test_cases(self,
                         queries: List[str],
                         outputs: List[str],
                         contexts: List[List[str]],
                         ground_truths: Optional[List[str]] = None) -> List[LLMTestCase]:
        """
        Crée des cas de test DeepEval
        
        Args:
            queries: Questions
            outputs: Réponses générées
            contexts: Contextes utilisés
            ground_truths: Réponses de référence
        """
        test_cases = []
        
        for i in range(len(queries)):
            test_case = LLMTestCase(
                input=queries[i],
                actual_output=outputs[i],
                retrieval_context=contexts[i],
                expected_output=ground_truths[i] if ground_truths else None
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def evaluate_pipeline(self,
                         retriever_pipeline,
                         generation_pipeline,
                         test_questions: List[str],
                         ground_truths: Optional[List[str]] = None,
                         metrics: Optional[List[str]] = None,
                         k: int = 3) -> Dict:
        """
        Évalue le pipeline avec DeepEval
        """
        outputs = []
        contexts = []
        
        # Exécuter le pipeline
        for question in test_questions:
            # Retrieval
            retrieved = retriever_pipeline.search(
                query=question,
                limit=k,
                use_hybrid=True
            )
            
            doc_contexts = [doc.get('text', '') for doc in retrieved]
            contexts.append(doc_contexts)
            
            # Génération
            response = generation_pipeline.generate(
                query=question,
                retrieved_docs=retrieved
            )
            
            outputs.append(response['response'] if response['success'] else "")
        
        # Créer les cas de test
        test_cases = self.create_test_cases(
            queries=test_questions,
            outputs=outputs,
            contexts=contexts,
            ground_truths=ground_truths
        )
        
        # Sélectionner les métriques
        selected_metrics = []
        if metrics:
            selected_metrics = [self.metrics[m] for m in metrics if m in self.metrics]
        else:
            selected_metrics = list(self.metrics.values())
        
        # Évaluer
        results = evaluate(
            test_cases=test_cases,
            metrics=selected_metrics
        )
        
        # Formater les résultats
        formatted_results = {
            "scores": {},
            "test_cases": []
        }
        
        for test_case in test_cases:
            formatted_results["test_cases"].append({
                "input": test_case.input,
                "actual_output": test_case.actual_output[:200] + "...",
                "metrics": {
                    name: metric.score 
                    for name, metric in self.metrics.items() 
                    if hasattr(metric, 'score')
                }
            })
            
        # # MAINTENANT on utilise les VRAIS résultats pour formater
        # formatted_results = {
        #     "scores": {},
        #     "test_cases": [],
        #     "summary": {},
        #     "success": True,
        #     "raw_results": results
        # }

        # # On extrait les scores depuis les métriques (qui ont été mises à jour par evaluate())
        # for metric in selected_metrics:
        #     metric_name = metric.__class__.__name__
        #     formatted_results["scores"][metric_name] = {
        #         "score": metric.score,
        #         "threshold": metric.threshold,
        #         "success": metric.is_successful(),
        #         "reason": metric.reason
        #     }
        
        return formatted_results