

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

class HyDEGenerator:
    """Génère un pseudo-document HyDE via Ollama."""

    def __init__(
        self,
        ollama_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 20,
    ):
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:7b")
        self.timeout = timeout

    def generate(self, query: str) -> Optional[str]:
        prompt = (
            "Rédige un paragraphe factuel et concis qui répondrait idéalement à la question.\n"
            "N'invente pas de format de réponse, écris uniquement le contenu hypothétique utile à la recherche.\n\n"
            f"Question: {query}\n\n"
            "Paragraphe hypothétique:"
        )
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 220,
                    },
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                logger.warning(f"⚠️ HyDE indisponible (status={response.status_code})")
                return None
            return response.json().get("response", "").strip() or None
        except Exception as e:
            logger.warning(f"⚠️ Erreur HyDE: {e}")
            return None