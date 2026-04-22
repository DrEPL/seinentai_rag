"""
Intent Router — SEINENTAI4US

Service d'orchestration intelligente qui classifie l'intention de chaque message
utilisateur et décide du routage :
  - small_talk       → réponse directe (LLM sans RAG)
  - knowledge_query  → pipeline RAG (agent ou statique)
  - ambiguous        → question de clarification
  - out_of_domain    → recadrage poli + invitation

Un seul appel LLM compact retourne à la fois la classification ET la réponse directe.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from pathlib import Path

from Agent.prompts import INTENT_CLASSIFIER_PROMPT, DIRECT_RESPONSE_SYSTEM_PROMPT

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class IntentClassification:
    """Résultat de la classification d'intention."""
    intent: str = "knowledge_query"        # small_talk | knowledge_query | ambiguous | out_of_domain
    confidence: float = 0.5
    reasoning: str = ""
    direct_response: str = ""              # Pré-rempli si small_talk / out_of_domain
    follow_up_question: str = ""           # Pré-rempli si ambiguous
    classification_time: float = 0.0       # Temps de classification en secondes

    @property
    def needs_rag(self) -> bool:
        """Retourne True si le message nécessite le pipeline RAG."""
        return self.intent == "knowledge_query"

    @property
    def is_direct(self) -> bool:
        """Retourne True si on peut répondre directement sans RAG."""
        return self.intent in ("small_talk", "out_of_domain", "ambiguous")


# ── Intent Router ─────────────────────────────────────────────────────────────

class IntentRouter:
    """
    Classifie l'intention utilisateur via un appel LLM compact.

    Un seul appel retourne la classification ET la réponse directe
    si applicable, pour minimiser la latence.
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL_NAME", "mistral-large-3:675b-cloud")
        logger.info("🧠 IntentRouter initialisé")

    def classify(
        self,
        message: str,
        conversation_context: str = "",
    ) -> IntentClassification:
        """
        Classifie le message utilisateur en une intention.

        Args:
            message: Le message de l'utilisateur.
            conversation_context: Contexte conversationnel (messages précédents).

        Returns:
            IntentClassification avec l'intention, la confiance, et la réponse.
        """
        start_time = time.time()

        # Raccourci : messages très courts et évidents (évite un appel LLM)
        quick = self._quick_classify(message, conversation_context)
        if quick is not None:
            quick.classification_time = time.time() - start_time
            logger.info(
                f"🧠 [IntentRouter] Quick classify: intent={quick.intent} "
                f"confidence={quick.confidence:.2f} ({quick.classification_time*1000:.0f}ms)"
            )
            return quick

        # Classification LLM
        prompt = INTENT_CLASSIFIER_PROMPT.format(
            message=message,
            conversation_context=conversation_context or "(Pas de contexte conversationnel)",
        )

        parsed = self._call_llm_json(prompt, temperature=0.1, max_tokens=512)
        classification_time = time.time() - start_time

        intent = parsed.get("intent", "knowledge_query")
        confidence = float(parsed.get("confidence", 0.5))
        reasoning = parsed.get("reasoning", "")
        direct_response = parsed.get("direct_response", "")
        follow_up = parsed.get("follow_up_question", "")

        # Validation : si intent inconnu, fallback sur knowledge_query
        valid_intents = {"small_talk", "knowledge_query", "ambiguous", "out_of_domain"}
        if intent not in valid_intents:
            logger.warning(f"🧠 Intent inconnu '{intent}', fallback → knowledge_query")
            intent = "knowledge_query"

        # Si confidence faible pour small_talk, traiter comme knowledge_query (safety)
        if intent == "small_talk" and confidence < 0.6:
            logger.info(f"🧠 Confiance trop faible pour small_talk ({confidence:.2f}), → knowledge_query")
            intent = "knowledge_query"
            direct_response = ""

        result = IntentClassification(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            direct_response=direct_response,
            follow_up_question=follow_up,
            classification_time=classification_time,
        )

        logger.info(
            f"🧠 [IntentRouter] LLM classify: intent={result.intent} "
            f"confidence={result.confidence:.2f} ({result.classification_time*1000:.0f}ms) "
            f"— {result.reasoning}"
        )
        return result

    # ── Quick classification (no LLM) ─────────────────────────────────────────

    def _quick_classify(
        self, message: str, conversation_context: str
    ) -> Optional[IntentClassification]:
        """
        Classification rapide sans appel LLM pour les cas évidents.

        Retourne None si le message nécessite une classification LLM.
        """
        clean = message.strip().lower()
        # Retirer la ponctuation de fin pour la comparaison
        clean_no_punct = re.sub(r"[!?.…,;:]+$", "", clean).strip()

        # ── Salutations évidentes ─────────────────────────────────────────
        greetings = {
            "bonjour", "bonsoir", "salut", "hello", "hi", "hey",
            "coucou", "yo", "wesh", "bonne journée", "bonne soirée",
            "bonne nuit", "bon matin", "bonne après-midi",
        }
        if clean_no_punct in greetings:
            return IntentClassification(
                intent="small_talk",
                confidence=0.99,
                reasoning="Salutation évidente",
                direct_response="",  # Sera généré par le LLM direct
            )

        # ── Remerciements évidents ────────────────────────────────────────
        thanks = {
            "merci", "merci beaucoup", "merci bien", "thanks", "thank you",
            "super merci", "ok merci", "parfait merci", "génial merci",
            "d'accord merci", "c'est noté merci",
        }
        if clean_no_punct in thanks:
            return IntentClassification(
                intent="small_talk",
                confidence=0.98,
                reasoning="Remerciement évident",
                direct_response="",
            )

        # ── Au revoir évidents ────────────────────────────────────────────
        goodbyes = {
            "au revoir", "à bientôt", "à plus", "bye", "à la prochaine",
            "bonne continuation", "ciao", "adieu",
        }
        if clean_no_punct in goodbyes:
            return IntentClassification(
                intent="small_talk",
                confidence=0.99,
                reasoning="Formule d'au revoir",
                direct_response="",
            )

        # ── Comment ça va ? ───────────────────────────────────────────────
        how_are_you = {
            "comment ça va", "ça va", "comment vas-tu", "tu vas bien",
            "comment allez-vous", "comment tu vas", "la forme",
        }
        if clean_no_punct in how_are_you:
            return IntentClassification(
                intent="small_talk",
                confidence=0.97,
                reasoning="Question sociale simple",
                direct_response="",
            )

        # Pas de classification rapide possible
        return None

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def _call_llm_json(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 512,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Appelle le LLM et parse la réponse en JSON."""
        for attempt in range(max_retries):
            raw = self._call_llm(prompt, temperature=temperature, max_tokens=max_tokens)
            if not raw:
                time.sleep(1)
                continue

            parsed = self._parse_json(raw)
            if parsed:
                return parsed

            logger.warning(f"🧠 Échec parsing JSON (tentative {attempt+1}/{max_retries})")
            time.sleep(0.5)

        logger.error("🧠 Toutes les tentatives de classification ont échoué")
        return {"intent": "knowledge_query", "confidence": 0.3, "reasoning": "Fallback (parsing échoué)"}

    def _call_llm(self, prompt: str, temperature: float = 0.1, max_tokens: int = 512) -> str:
        """Appelle Ollama et retourne le texte brut."""
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=body, timeout=60)
            if resp.status_code != 200:
                logger.error(f"🧠 LLM error {resp.status_code}: {resp.text[:200]}")
                return ""
            return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"🧠 LLM call failed: {e}")
            return ""

    def _call_llm_stream(self, prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 1024):
        """Appelle Ollama en mode streaming et yield les tokens."""
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system:
            body["system"] = system

        try:
            with requests.post(f"{self.base_url}/api/generate", json=body, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        decoded = json.loads(line.decode("utf-8"))
                        token = decoded.get("response", "")
                        if token:
                            yield token
                        if decoded.get("done"):
                            break
        except Exception as e:
            logger.error(f"🧠 LLM stream call failed: {e}")
            yield ""

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        """Extrait le premier bloc JSON d'une réponse LLM."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Chercher un bloc ```json ... ```
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Chercher le premier { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        return {}


# ── Lazy Singleton ────────────────────────────────────────────────────────────

_intent_router: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """Retourne le singleton IntentRouter (lazy init)."""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router
