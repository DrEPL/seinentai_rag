# evaluation/metrics_config.py
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from deepeval.models import DeepEvalBaseLLM
import logging

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

class OllamaRagasLLM:
    """Wrapper pour utiliser Ollama avec RAGAS"""
    
    def __init__(self, temperature: float = 0):
        self.model_name = os.getenv('RAGAS_MODEL_NAME', '')
        self.temperature = temperature
        self.llm = self._init_llm()
        
    def _init_llm(self):
        """Initialise le LLM Ollama"""
        return ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        )
    
    def get_ragas_llm(self):
        """Retourne le wrapper RAGAS"""
        return LangchainLLMWrapper(self.llm)

class SentenceEmbeddings:
    """Wrapper pour les embeddings Sentence Transformers"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = self._init_embeddings()
        
    def _init_embeddings(self):
        """Initialise les embeddings"""
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def get_ragas_embeddings(self):
        """Retourne le wrapper RAGAS"""
        return LangchainEmbeddingsWrapper(self.embeddings)

class OllamaDeepEvalModel(DeepEvalBaseLLM):
    """Modèle personnalisé pour DeepEval avec Ollama"""
    
    def __init__(self):
        DEEP_EVAL_MODEL_NAME = os.getenv('DEEP_EVAL_MODEL_NAME', '')
        self.model_name = DEEP_EVAL_MODEL_NAME
        self.ollama_client = ChatOllama(
            model=DEEP_EVAL_MODEL_NAME,
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        )
        
    def load_model(self):
        """Charge le modèle"""
        return self.ollama_client
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Génère une réponse"""
        model = self.load_model()
        response = model.invoke(prompt)
        return response.content
    
    async def a_generate(self, prompt: str, **kwargs) -> str:
        """Version asynchrone"""
        return self.generate(prompt, **kwargs)
    
    def get_model_name(self) -> str:
        """Retourne le nom du modèle"""
        return f"Ollama-{self.model_name}"