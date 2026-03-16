
import logging
from typing import Dict, Any


logger = logging.getLogger(__name__)

# Fonction utilitaire pour intégrer avec votre pipeline existant
def rag_complete_pipeline(
    query: str,
    retriever_pipeline,
    generation_pipeline,
    limit: int = 5,
    score_threshold: float = 0.3,
    use_hybrid: bool = True,
    **gen_kwargs
) -> Dict[str, Any]:
    """
    Pipeline RAG complet: retrieve + generate
    
    Args:
        query: Question de l'utilisateur
        retriever_pipeline: Instance de RetrieverPipeline
        generation_pipeline: Instance de GenerationPipeline
        limit: Nombre de documents à récupérer
        score_threshold: Seuil de pertinence entre 0.0 et 1.0
        use_hybrid: Utiliser la recherche hybride
        **gen_kwargs: Arguments pour la génération
        
    Returns:
        Réponse complète avec sources
    """
    # 1. RETRIEVE - Récupérer les documents pertinents
    logger.info(f"🔍 Étape 1: Retrieval pour '{query}'")
    retrieved_docs = retriever_pipeline.search(
        query=query,
        limit=limit,
        score_threshold=score_threshold,
        use_hybrid=use_hybrid
    )
    
    if not retrieved_docs:
        logger.warning("⚠️ Aucun document pertinent trouvé")
        return {
            "success": False,
            "error": "Aucun document pertinent trouvé",
            "query": query,
            "response": "Je n'ai pas trouvé d'information pertinente dans la base de connaissances."
        }
    
    logger.info(f"✅ {len(retrieved_docs)} documents récupérés")
    
    # 2. GENERATE - Générer la réponse
    logger.info(f"🤖 Étape 2: Génération avec {generation_pipeline.model_name}")
    result = generation_pipeline.generate_with_sources(
        query=query,
        retrieved_docs=retrieved_docs,
        **gen_kwargs
    )
    
    # Ajouter la requête au résultat
    result["query"] = query
    
    return result