import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Classe utilitaire pour découper du texte en chunks utilisant LangChain.

    Cette classe fournit différentes stratégies de découpage de texte :
    - Découpage récursif (par défaut) : utilise une hiérarchie de séparateurs
    - Découpage par caractères simples
    - Découpage par phrases ou paragraphes (via séparateurs personnalisés)

    Chaque chunk contient le texte découpé ainsi que des métadonnées
    pour faciliter le suivi et la recherche.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialise le TextChunker avec les paramètres de découpage.

        Args:
            chunk_size: Taille maximale de chaque chunk en caractères
            chunk_overlap: Nombre de caractères de chevauchement entre chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Séparateurs par défaut pour le découpage récursif
        # LangChain essaie d'abord les séparateurs principaux, puis les secondaires
        self.default_separators = ["\n\n", "\n", ". ", " ", ""]

        # Configuration des différents splitters LangChain
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.default_separators,
            length_function=len,  # Fonction de calcul de longueur (caractères)
            is_separator_regex=False  # Les séparateurs sont des chaînes simples
        )

        self.character_splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separator=" ",  # Séparation par espaces
            length_function=len
        )

    def chunk_text(self, text: str, method: str = 'recursive') -> List[Dict[str, Any]]:
        """
        Découpe le texte en chunks selon la méthode spécifiée.

        Args:
            text: Texte à découper
            method: Méthode de découpage ('recursive', 'character', 'sentence', 'paragraph')

        Returns:
            Liste de dictionnaires contenant chaque chunk avec ses métadonnées :
            - text: contenu du chunk
            - start_char: position de début dans le texte original
            - end_char: position de fin dans le texte original
            - chunk_index: index du chunk dans la liste
            - total_chunks: nombre total de chunks
            - doc_id: identifiant du document (sera défini dans chunk_with_metadata)
            - filename: nom du fichier source (sera défini dans chunk_with_metadata)
            - metadata: métadonnées supplémentaires
        """
        logger.info(f"🔄 Découpage du texte avec méthode '{method}' (taille: {self.chunk_size}, chevauchement: {self.chunk_overlap})")

        # Sélection du splitter selon la méthode
        if method == 'character':
            # Découpage simple par caractères
            splitter = self.character_splitter
        elif method == 'sentence':
            # Utilise RecursiveCharacterTextSplitter avec séparateurs de phrases
            sentence_separators = [". ", "! ", "? ", "\n\n", "\n", " ", ""]
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=sentence_separators,
                length_function=len
            )
        elif method == 'paragraph':
            # Utilise RecursiveCharacterTextSplitter avec séparateurs de paragraphes
            paragraph_separators = ["\n\n", "\n", ". ", " ", ""]
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=paragraph_separators,
                length_function=len
            )
        else:  # 'recursive' par défaut
            # Utilise le RecursiveCharacterTextSplitter configuré
            splitter = self.recursive_splitter

        # Conversion du texte en Document LangChain pour le traitement
        doc = Document(page_content=text)

        # Découpage du document
        langchain_chunks = splitter.split_documents([doc])

        # Conversion en format uniforme avec métadonnées de position
        chunks = []
        current_position = 0

        for i, chunk_doc in enumerate(langchain_chunks):
            chunk_text = chunk_doc.page_content

            # Calcul des positions approximatives dans le texte original
            # Note: Cette approximation peut être inexacte avec le chevauchement
            start_char = text.find(chunk_text, current_position)
            if start_char == -1:  # Si pas trouvé exactement, utiliser la position courante
                start_char = current_position
            end_char = start_char + len(chunk_text)

            chunks.append({
                'text': chunk_text,
                'start_char': start_char,
                'end_char': end_char,
                'chunk_index': i,
                'total_chunks': len(langchain_chunks),
                'doc_id': None,  # Sera défini dans chunk_with_metadata
                'filename': None,  # Sera défini dans chunk_with_metadata
                'metadata': {}  # Sera enrichi dans chunk_with_metadata
            })

            # Mise à jour de la position pour le chunk suivant
            current_position = max(current_position + len(chunk_text) - self.chunk_overlap, end_char)

        logger.info(f"✅ Texte découpé en {len(chunks)} chunks")
        return chunks

    def chunk_with_metadata(self, text: str, doc_id: str, filename: str,
                           metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Découpe le texte et ajoute des métadonnées complètes à chaque chunk.

        Cette méthode est utile pour préparer les chunks avant indexation
        dans une base de données vectorielle ou un système RAG.

        Args:
            text: Texte à découper
            doc_id: Identifiant unique du document
            filename: Nom du fichier source
            metadata: Métadonnées supplémentaires à ajouter

        Returns:
            Liste de chunks enrichis avec métadonnées complètes (format uniforme)
        """
        # Découpage du texte (format de base)
        chunks = self.chunk_text(text)

        # Métadonnées de base
        base_metadata = {
            'doc_id': doc_id,
            'filename': filename,
            'chunker_config': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'library': 'langchain'
            }
        }

        # Fusion avec métadonnées utilisateur
        if metadata:
            base_metadata.update(metadata)

        # Enrichissement de chaque chunk avec les métadonnées complètes
        for chunk in chunks:
            chunk['doc_id'] = doc_id
            chunk['filename'] = filename
            chunk['metadata'] = base_metadata.copy()  # Copie pour éviter les références partagées

        logger.info(f"📋 Métadonnées ajoutées à {len(chunks)} chunks pour le document '{filename}'")
        return chunks