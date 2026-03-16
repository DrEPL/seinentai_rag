"""
Fichier de fonctions utilitaires pour le traitement de documents
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os

# Configuration du logging
logger = logging.getLogger(__name__)

# ==================== Fonctions de génération d'IDs ====================

def generate_doc_id(filename: str, content_hash: str) -> str:
    """
    Génère un ID unique pour un document
    
    Args:
        filename: Nom du fichier
        content_hash: Hash du contenu
    
    Returns:
        ID unique du document
    """
    unique_str = f"{filename}_{content_hash}_{datetime.now().isoformat()}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """
    Génère un ID unique pour un chunk
    
    Args:
        doc_id: ID du document parent
        chunk_index: Index du chunk
    
    Returns:
        ID unique du chunk
    """
    unique_str = f"{doc_id}_chunk_{chunk_index}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def generate_batch_id() -> str:
    """
    Génère un ID unique pour un batch de traitement
    
    Returns:
        ID unique du batch
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = hashlib.md5(os.urandom(8)).hexdigest()[:8]
    return f"batch_{timestamp}_{random_suffix}"


# ==================== Fonctions de validation ====================

def validate_content(content: bytes, filename: str) -> bool:
    """
    Valide que le contenu n'est pas vide
    
    Args:
        content: Contenu binaire du fichier
        filename: Nom du fichier (pour logging)
    
    Returns:
        True si valide, False sinon
    """
    if not content:
        logger.warning(f"⚠️ Contenu vide pour {filename}")
        return False
    
    if len(content) == 0:
        logger.warning(f"⚠️ Taille zéro pour {filename}")
        return False
    
    return True


def validate_text(text: str, filename: str) -> bool:
    """
    Valide que le texte n'est pas vide
    
    Args:
        text: Texte extrait
        filename: Nom du fichier (pour logging)
    
    Returns:
        True si valide, False sinon
    """
    if not text or not text.strip():
        logger.warning(f"⚠️ Texte vide pour {filename}")
        return False
    
    return True


def validate_chunks(chunks: List[Dict], filename: str) -> bool:
    """
    Valide que les chunks sont corrects
    
    Args:
        chunks: Liste des chunks
        filename: Nom du fichier (pour logging)
    
    Returns:
        True si valide, False sinon
    """
    if not chunks:
        logger.warning(f"⚠️ Aucun chunk pour {filename}")
        return False
    
    for i, chunk in enumerate(chunks):
        if 'text' not in chunk:
            logger.error(f"❌ Chunk {i} sans texte pour {filename}")
            return False
        if not chunk['text'].strip():
            logger.warning(f"⚠️ Chunk {i} vide pour {filename}")
            return False
    
    return True


def validate_embeddings(embeddings: List, expected_count: int, filename: str) -> bool:
    """
    Valide les embeddings
    
    Args:
        embeddings: Liste des embeddings
        expected_count: Nombre attendu
        filename: Nom du fichier (pour logging)
    
    Returns:
        True si valide, False sinon
    """
    if not embeddings:
        logger.error(f"❌ Embeddings vides pour {filename}")
        return False
    
    if len(embeddings) != expected_count:
        logger.error(f"❌ Nombre embeddings ({len(embeddings)}) != chunks ({expected_count})")
        return False
    
    # Vérifier que chaque embedding a la bonne dimension
    embedding_dim = len(embeddings[0]) if embeddings else 0
    for i, emb in enumerate(embeddings):
        if len(emb) != embedding_dim:
            logger.error(f"❌ Dimension embedding {i} incorrecte pour {filename}")
            return False
    
    return True


# ==================== Fonctions de métadonnées ====================

def create_document_metadata(
    bucket: str,
    filename: str,
    content_hash: str,
    additional_metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Crée les métadonnées pour un document
    
    Args:
        bucket: Bucket MinIO
        filename: Nom du fichier
        content_hash: Hash du contenu
        additional_metadata: Métadonnées supplémentaires
    
    Returns:
        Dictionnaire des métadonnées
    """
    metadata = {
        'bucket': bucket,
        'filename': filename,
        'content_hash': content_hash,
        'processed_at': datetime.now().isoformat(),
        'file_extension': os.path.splitext(filename)[1].lower(),
        'file_name_without_ext': os.path.splitext(filename)[0]
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return metadata


def create_chunk_metadata(
    doc_id: str,
    chunk_index: int,
    chunk_text: str,
    additional_metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Crée les métadonnées pour un chunk
    
    Args:
        doc_id: ID du document
        chunk_index: Index du chunk
        chunk_text: Texte du chunk
        additional_metadata: Métadonnées supplémentaires
    
    Returns:
        Dictionnaire des métadonnées du chunk
    """
    metadata = {
        'doc_id': doc_id,
        'chunk_id': generate_chunk_id(doc_id, chunk_index),
        'chunk_index': chunk_index,
        'chunk_size': len(chunk_text),
        'chunk_word_count': len(chunk_text.split())
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return metadata


# ==================== Fonctions de logging ====================

def log_processing_start(filename: str, bucket: str) -> None:
    """Log le début du traitement"""
    logger.info(f"🔄 Début traitement: {bucket}/{filename}")


def log_processing_success(filename: str, chunk_count: int) -> None:
    """Log le succès du traitement"""
    logger.info(f"✅ Traitement réussi: {filename} ({chunk_count} chunks)")


def log_processing_error(filename: str, error: Exception) -> None:
    """Log une erreur de traitement"""
    logger.error(f"❌ Erreur traitement {filename}: {str(error)}")
    logger.debug(traceback.format_exc())


# ==================== Fonctions de formatage ====================

def format_file_size(size_bytes: int) -> str:
    """
    Formate la taille d'un fichier en format lisible
    
    Args:
        size_bytes: Taille en bytes
    
    Returns:
        Taille formatée (ex: "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Tronque un texte pour l'affichage
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
    
    Returns:
        Texte tronqué
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


# ==================== Fonctions de sauvegarde ====================

def save_metadata_to_json(metadata: Dict, output_dir: str, filename: str) -> str:
    """
    Sauvegarde des métadonnées dans un fichier JSON
    
    Args:
        metadata: Métadonnées à sauvegarder
        output_dir: Dossier de sortie
        filename: Nom du fichier original
    
    Returns:
        Chemin du fichier JSON créé
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(filename)[0]
    json_filename = f"{base_name}_metadata_{timestamp}.json"
    json_path = os.path.join(output_dir, json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Métadonnées sauvegardées: {json_path}")
    return json_path


# ==================== Initialisation ====================

# Importer traceback pour les logs d'erreur
import traceback