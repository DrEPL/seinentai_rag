import logging
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv
from pathlib import Path

from seinentai4us_api.utils.functions import build_prompt, format_context, get_default_system_prompt

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

class GenerationPipeline:
    """
    Pipeline de génération de réponses utilisant un LLM via Ollama
    """
    
    # Templates de prompts pour différents cas d'usage

    def __init__(
        self,
        system_prompt: Optional[str] = None
    ):
        """
        Initialise le pipeline de génération
        
        Args:
            system_prompt: Prompt système optionnel
        """
        print("Env: ", os.getenv('OLLAMA_MODEL_NAME'))
        self.model_name = os.getenv('OLLAMA_MODEL_NAME', 'mistral-large-3:675b-cloud')
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        
        self.temperature = os.getenv('DEFAULT_TEMPERATURE', 0.7)
        self.max_tokens = os.getenv('DEFAULT_MAX_TOKENS', 2048)
        self.template_name = os.getenv('DEFAULT_TEMPLATE', 'default')
        self.system_prompt = system_prompt or get_default_system_prompt()
        
        # Vérifier la disponibilité du modèle
        self._check_model_available()
    
    def _check_model_available(self):
        """Vérifie que le modèle est disponible dans Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                
                if self.model_name not in available_models:
                    logger.warning(f"⚠️ Modèle '{self.model_name}' non trouvé. Modèles disponibles: {available_models}")
                    logger.info(f"💡 Pour installer: ollama pull {self.model_name}")
                else:
                    logger.info(f"✅ Modèle '{self.model_name}' disponible")
            else:
                logger.warning(f"⚠️ Impossible de vérifier les modèles Ollama: {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connexion à Ollama impossible sur {self.ollama_base_url}")
            logger.info("💡 Assurez-vous qu'Ollama est lancé: 'ollama serve'")
        except Exception as e:
            logger.error(f"❌ Erreur vérification modèle: {e}")
    
    def generate(self, query: str, retrieved_docs: List[Dict[str, Any]], template_name: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None, stream: bool = False, callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Génère une réponse à partir de la requête et des documents
        
        Args:
            query: Question de l'utilisateur
            retrieved_docs: Documents récupérés par le retriever
            template_name: Template à utiliser (optionnel)
            temperature: Température pour cette génération (optionnel)
            max_tokens: Max tokens pour cette génération (optionnel)
            stream: Activer le streaming de la réponse
            callback: Fonction callback pour le streaming
            
        Returns:
            Dictionnaire avec la réponse et les métadonnées
        """
        try:
            # 1. Formater le contexte
            context = format_context(retrieved_docs)
            logger.debug(f"Contexte formaté ({len(retrieved_docs)} docs):\n{context[:200]}...")
            
            # 2. Construire le prompt
            prompt = build_prompt(self, query, context, template_name)
            logger.debug(f"Prompt:\n{prompt[:200]}...")
            
            # 3. Préparer la requête Ollama
            ollama_request = {
                "model": self.model_name,
                "prompt": prompt,
                "system": self.system_prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature or self.temperature,
                    "num_predict": max_tokens or self.max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            # 4. Appeler Ollama
            start_time = datetime.now()
            
            if stream:
                return self._generate_stream(ollama_request, callback)
            else:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=ollama_request,
                    timeout=120
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Erreur Ollama: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Erreur API: {response.status_code}",
                        "response": None
                    }
                
                result = response.json()
                
                # 5. Calculer le temps de génération
                generation_time = (datetime.now() - start_time).total_seconds()
                
                # 6. Retourner la réponse avec métadonnées
                return {
                    "success": True,
                    "response": result.get('response', '').strip(),
                    "model": self.model_name,
                    "generation_time": generation_time,
                    "prompt_tokens": result.get('prompt_eval_count', 0),
                    "completion_tokens": result.get('eval_count', 0),
                    "total_docs_used": len(retrieved_docs),
                    "temperature": temperature or self.temperature,
                    "template": template_name or self.template_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout de l'API Ollama")
            return {
                "success": False,
                "error": "Timeout de l'API Ollama",
                "response": None
            }
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def _generate_stream(self, request: Dict, callback: Optional[callable] = None):
        """
        Gère le streaming de la réponse
        
        Args:
            request: Requête Ollama
            callback: Fonction appelée pour chaque chunk
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=request,
                stream=True,
                timeout=120
            )
            
            full_response = []
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        if callback:
                            callback(chunk['response'])
                        full_response.append(chunk['response'])
                    
                    if chunk.get('done', False):
                        return {
                            "success": True,
                            "response": ''.join(full_response),
                            "model": self.model_name,
                            "prompt_tokens": chunk.get('prompt_eval_count', 0),
                            "completion_tokens": chunk.get('eval_count', 0)
                        }
                        
        except Exception as e:
            logger.error(f"❌ Erreur streaming: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def generate_with_sources(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Génère une réponse et inclut les sources utilisées
        
        Args:
            query: Question de l'utilisateur
            retrieved_docs: Documents récupérés
            **kwargs: Arguments additionnels pour generate()
            
        Returns:
            Réponse avec les sources
        """
        result = self.generate(query, retrieved_docs, **kwargs)
        
        if result["success"]:
            # Ajouter les sources
            sources = []
            for doc in retrieved_docs:
                sources.append({
                    "filename": doc.get('filename', doc.get('metadata', {}).get('filename', 'Inconnu')),
                    "text": doc.get('text', '')[:200] + "...",  # Extrait
                    "score": doc.get('score', 0),
                    "chunk_index": doc.get('chunk_index', doc.get('metadata', {}).get('chunk_index', 0))
                })
            
            result["sources"] = sources
            
            # Statistiques sur les sources
            unique_files = set(s["filename"] for s in sources)
            result["source_stats"] = {
                "total_sources": len(sources),
                "unique_files": len(unique_files),
                "avg_score": sum(s["score"] for s in sources) / len(sources) if sources else 0
            }
        
        return result
    
    def list_available_models(self) -> List[str]:
        """Liste les modèles disponibles dans Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except:
            pass
        return []


