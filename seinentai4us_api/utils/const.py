from typing import List

# ── Documents (extensions supportées) ───────────────────────────────────
SUPPORTED_DOCUMENT_EXTENSIONS: List[str] = [
    ".pdf",
    ".docx",
    ".md",
    ".markdown",
    ".txt",
    ".csv",
    ".json",
]

PROMPT_TEMPLATES = {
    "default": """Tu es un assistant IA spécialisé dans la réponse à des questions basées sur des documents fournis.
    Utilise UNIQUEMENT les informations des documents ci-dessous pour répondre à la question.
    Si l'information n'est pas présente dans les documents, dis-le honnêtement sans inventer.

    DOCUMENTS CONTEXTUELS:
    {context}

    QUESTION: {query}

    RÉPONSE (basée uniquement sur les documents fournis):""",

    "concise": """Contexte: {context}

    Question: {query}

    Réponse concise (basée uniquement sur le contexte):""",

    "detailed": """Tu es un expert analyste de documents. Voici des extraits de documents pertinents:

    {context}
    Sur la base de ces extraits uniquement, réponds à la question suivante de façon détaillée:
    {query}

    Détaillé ta réponse en citant les parties pertinentes des documents:""",
}