import logging
import uuid
from typing import List, Dict, Any, Optional
import heapq
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance
from fastembed import SparseTextEmbedding

from seinentai4us_api.utils.functions import generate_chunk_id

logger = logging.getLogger(__name__)

class VectorStore:
    """Stockage vectoriel avec Qdrant supportant recherche hybride (dense + sparse)"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 6333, 
                 collection_name: str = "documents",
                 vector_size: int = 384,
                 sparse_vector_name: str = "keywords",
                 sparse_model_name: str = "Qdrant/bm25",
                 client: Optional[QdrantClient] = None,
                 sparse_model: Optional[SparseTextEmbedding] = None):
        """
        Args:
            host: Hôte Qdrant
            port: Port Qdrant
            collection_name: Nom de la collection
            vector_size: Dimension des vecteurs denses (embeddings)
            sparse_vector_name: Nom du vecteur sparse pour BM25
            sparse_model_name: Nom du model sparse Ex: Qdrant/bm25, Qdrant/minicoil-v1, prithivida/Splade_PP_en_v1
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.sparse_vector_name = sparse_vector_name
        self.client = client
        
        # Initialiser le modèle sparse (optionnel - si tu veux générer ici)
        if sparse_model is not None:
            self.sparse_model = sparse_model
        else:
            try:
                self.sparse_model = SparseTextEmbedding(sparse_model_name)
                logger.info(f"✅ Modèle sparse chargé: {sparse_model_name}")
            except Exception as e:
                logger.warning(f"⚠️ Modèle sparse non chargé: {e}")
                self.sparse_model = None

        if self.client is None:
            self._connect()
        else:
            # On suppose que le client est déjà géré par ailleurs (singleton).
            try:
                self.client.get_collections()
                logger.info(f"✅ Client Qdrant injecté {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"❌ Erreur connexion Qdrant (client injecté): {e}")
                raise
    
    def _connect(self):
        """Établit la connexion à Qdrant"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            # Tester la connexion
            self.client.get_collections()
            logger.info(f"✅ Connecté à Qdrant {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Qdrant: {e}")
            raise
    
    def create_collection(self, vector_size: int = 384, distance: Distance = Distance.COSINE, force_recreate: bool = False):
        """
        Crée la collection avec support des vecteurs denses ET sparse
        
        Args:
            force_recreate: Si True, supprime et recrée la collection
        """
        try:
            # Vérifier si la collection existe
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                if force_recreate:
                    logger.warning(f"🗑️ Suppression de la collection '{self.collection_name}'")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"ℹ Collection '{self.collection_name}' existe déjà")
                    # Vérifier la configuration actuelle
                    collection_info = self.client.get_collection(self.collection_name)
                    logger.info(f"   Configuration: dense={collection_info.config.params.vectors}")
                    logger.info(f"   Sparse: {collection_info.config.params.sparse_vectors}")
                    return
            
            sparse_vectors_config = {
                self.sparse_vector_name: models.SparseVectorParams(   # Vecteur sparse
                    index=models.SparseIndexParams(
                        on_disk=False,
                        full_scan_threshold=20000
                    )
                )}
            # Configuration des vecteurs
            vectors_config = {
                # Vecteur dense par défaut (nom vide "")
                "": models.VectorParams(
                    size=self.vector_size,
                    distance=distance
                ),
                # Vecteur sparse pour BM25
                # self.sparse_vector_name: models.SparseVectorParams(
                #     index=models.SparseIndexParams(
                #         on_disk=False,  # Garder en RAM pour performance
                #         full_scan_threshold=20000  # Seuil pour full scan
                #     )
                # )
            }
            
            # Créer la collection
            self.client.create_collection(
                collection_name=self.collection_name,
                sparse_vectors_config=sparse_vectors_config,
                vectors_config=vectors_config,
                # Optimisations
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000,  # Index après 20k points
                    memmap_threshold=50000      # Memmap après 50k points
                ),
                # Créer des index sur les champs fréquemment filtrés
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100
                )
            )
            
            logger.info(f"✅ Collection '{self.collection_name}' créée avec:")
            logger.info(f"   - Dense vector (dim={self.vector_size})")
            logger.info(f"   - Sparse vector '{self.sparse_vector_name}'")
            
            # Créer des index sur les payloads pour les filtres
            self._create_payload_indexes()
            
        except Exception as e:
            logger.error(f"❌ Erreur création collection: {e}")
            raise
        
    def generate_sparse_vector(self, text: str, top_k: int = 30) -> Optional[Dict]:
        """
        Génère un vecteur sparse à partir d'un texte et ne garde que les top_k
        
        Args:
            text: Texte à convertir
            top_k: Nombre maximum d'indices/values à garder (les plus importants)
            
        Returns:
            Dict avec 'indices' et 'values' réduits aux top_k
        """
        if not self.sparse_model:
            logger.error("❌ Modèle sparse non disponible")
            return None
        
        try:
            # Générer le vecteur sparse complet
            vectors = list(self.sparse_model.embed([text]))
            sparse_vector = vectors[0]
            
            # Récupérer les indices et valeurs
            indices = sparse_vector.indices.tolist()
            values = sparse_vector.values.tolist()
            
            # Créer une liste de paires (poids, index) pour trier
            pairs = list(zip(values, indices))
            
            # Trier par poids décroissant
            pairs.sort(reverse=True)
            
            # Garder seulement les top_k
            top_pairs = pairs[:top_k]
            
            # Reconstruire les listes triées par indice (optionnel, Qdrant s'en fiche)
            top_values = [p[0] for p in top_pairs]
            top_indices = [p[1] for p in top_pairs]
            
            return {
                "indices": top_indices,
                "values": top_values
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur génération sparse: {e}")
            return None

    def generate_sparse_vectors(self, texts: List[str], top_k: int = 30) -> List[Optional[Dict]]:
        """Génère des vecteurs sparse en batch pour une liste de textes."""
        if not texts:
            return []
        if not self.sparse_model:
            return [None] * len(texts)

        sparse_vectors: List[Optional[Dict]] = []
        try:
            vectors = list(self.sparse_model.embed(texts))
            for sparse_vector in vectors:
                indices = sparse_vector.indices.tolist()
                values = sparse_vector.values.tolist()
                if not indices:
                    sparse_vectors.append(None)
                    continue

                top_pairs = heapq.nlargest(top_k, zip(values, indices), key=lambda pair: pair[0])
                sparse_vectors.append({
                    "indices": [pair[1] for pair in top_pairs],
                    "values": [pair[0] for pair in top_pairs]
                })
            return sparse_vectors
        except Exception as e:
            logger.error(f"❌ Erreur génération sparse batch: {e}")
            return [None] * len(texts)
    
    def _create_payload_indexes(self):
        """Crée des index sur les champs fréquemment utilisés"""
        try:
            # Index sur filename pour filtrage rapide
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="filename",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index sur doc_id
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="doc_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index sur chunk_index
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="chunk_index",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            
            logger.info("✅ Index sur payloads créés")
        except Exception as e:
            logger.warning(f"⚠️ Erreur création index payloads: {e}")
    
    def index_documents(self, 
                       chunks: List[Dict[str, Any]], 
                       embeddings: List[np.ndarray],
                       generate_sparse: bool = True,
                       doc_id: Optional[str] = None,
                       batch_size: int = 100,
                       sparse_top_k: int = 30) -> bool:
        """
        Indexe des chunks avec leurs embeddings et vecteurs sparse optionnels
        
        Args:
            chunks: Liste de chunks avec métadonnées
            embeddings: Liste d'embeddings denses
            sparse_vectors: Liste optionnelle de vecteurs sparse (indices/values)
                           Format: [{'indices': [1,42], 'values': [0.22, 0.8]}, ...]
            
        Returns:
            True si succès
        """
        if len(chunks) != len(embeddings):
            logger.error("❌ Nombre de chunks et d'embeddings différent")
            return False

        chunk_texts = [chunk.get("text", "") for chunk in chunks]
        sparse_vectors: List[Optional[Dict]] = [None] * len(chunks)
        if generate_sparse and self.sparse_model:
            sparse_vectors = self.generate_sparse_vectors(chunk_texts, top_k=sparse_top_k)

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Utiliser un ID déterministe basé sur doc_id et chunk_index
            current_doc_id = chunk.get("doc_id") or doc_id
            chunk_index = chunk.get("chunk_index", i)
            if current_doc_id is not None:
                point_id = generate_chunk_id(doc_id=current_doc_id, chunk_index=chunk_index)
            else:
                # Fallback compatible si doc_id absent
                point_id = str(uuid.uuid4())
            
            # Préparer les vecteurs
            vector_dict = {
                "": embedding.tolist()  # Vecteur dense par défaut
            }
            
            # Générer et ajouter le vecteur sparse si demandé
            if generate_sparse and self.sparse_model:
                sparse_vector = sparse_vectors[i]
                if sparse_vector:
                    vector_dict[self.sparse_vector_name] = sparse_vector
                    logger.debug(f"✅ Sparse vector généré pour chunk {chunk_index}")

            chunk_metadata = chunk.get('metadata', {})
            parent_chunk_id = (
                chunk.get('parent_chunk_id')
                or chunk_metadata.get('parent_chunk_id')
                or f"{current_doc_id or chunk.get('filename', 'unknown')}:{chunk_index}"
            )
            parent_chunk_text = (
                chunk.get('parent_text')
                or chunk_metadata.get('parent_text')
                or chunk.get('text', '')
            )
            
            # Préparer les métadonnées
            payload = {
                'text': chunk['text'],
                'doc_id': current_doc_id or 'unknown',
                'filename': chunk.get('filename', 'unknown'),
                'chunk_index': chunk_index,
                'total_chunks': chunk.get('total_chunks', 1),
                'processed_at': chunk_metadata.get('processed_at', ''),
                'parent_chunk_id': parent_chunk_id,
                'parent_chunk_text': parent_chunk_text,
                'parent_chunk_order': chunk.get('parent_chunk_order', chunk_metadata.get('parent_chunk_order', chunk_index)),
                'metadata': chunk_metadata
            }
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector_dict,
                payload=payload
            ))
        
        try:
            # Upload par batch
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            logger.info(f"✅ {len(points)} documents indexés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur indexation: {e}")
            return False
    
    def search(self, 
               query_embedding: np.ndarray,
               limit: int = 20,
               score_threshold: float = 0.2,
               filter_condition: Optional[Dict] = None) -> List[Dict]:
        """
        Recherche dense classique
        
        Args:
            query_embedding: Vecteur dense de la requête
            limit: Nombre de résultats
            score_threshold: Seuil de score minimal entre 0.0 et 1.0    
            filter_condition: Filtres optionnels (ex: {"filename": "doc.pdf"})
            
        Returns:
            Liste des documents similaires
        """
        try:
            # Construire le filtre si nécessaire
            query_filter = self._build_query_filter(filter_condition)
            
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )

            documents = []
            for point in results.points:
                documents.append({
                    'id': str(point.id),
                    'score': point.score,
                    'text': point.payload.get('text', ''),
                    'filename': point.payload.get('filename', ''),
                    'chunk_index': point.payload.get('chunk_index', 0),
                    'doc_id': point.payload.get('doc_id', ''),
                    'metadata': point.payload
                })
            
            logger.info(f"✅ {len(documents)} résultats trouvés (dense search)")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche dense: {e}")
            return []
        
    def _build_query_filter(self, filter_condition: Optional[Dict]) -> Optional[models.Filter]:
        """Construit un filtre Qdrant à partir d'un dictionnaire simple."""
        if not filter_condition:
            return None

        must_conditions = []
        for key, value in filter_condition.items():
            must_conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
            )
        return models.Filter(must=must_conditions)
    
    def hybrid_search(self,
                     query_embedding: np.ndarray,
                     query_text: str,
                     limit: int = 10,
                     dense_limit: int = 20,
                     sparse_limit: int = 20,
                     fusion_method: str = "rrf",
                     score_threshold: float = 0.0,
                     filter_condition: Optional[Dict] = None) -> List[Dict]:
        """
        Recherche hybride combinant vecteurs dense et sparse
        
        Args:
            query_embedding: Vecteur dense de la requête
            query_text: Texte de la requête (pour générer le sparse vector)
            limit: Nombre final de résultats
            dense_limit: Nombre de résultats pour la recherche dense
            sparse_limit: Nombre de résultats pour la recherche sparse
            fusion_method: "rrf" ou "dbsf"
            score_threshold: Seuil de score
            filter_condition: Filtres optionnels
            
        Returns:
            Liste des documents fusionnés
        """
        try:
            # Construire le filtre si nécessaire
            query_filter = self._build_query_filter(filter_condition)
            
            # Préparer les prefetch
            prefetch = []
            
            # 1. Prefetch dense
            prefetch.append(
                models.Prefetch(
                    query=query_embedding.tolist(),
                    using="",  # Vecteur dense par défaut
                    limit=dense_limit,
                    filter=query_filter
                )
            )
            
            # 2. Prefetch sparse si fourni
            # Ajouter recherche sparse si possible
            if self.sparse_model:
                sparse_vector = self.generate_sparse_vector(query_text)
                if sparse_vector:
                    prefetch.append(
                        models.Prefetch(
                            query=sparse_vector,
                            using=self.sparse_vector_name,
                            limit=sparse_limit,
                            filter=query_filter
                        )
                    )
                    logger.info("✅ Recherche sparse ajoutée")
                else:
                    logger.warning("⚠️ Impossible de générer le vecteur sparse")
            else:
                logger.warning("⚠️ Modèle sparse non disponible")
            
            # Fusion (RRF par défaut)
            fusion = models.FusionQuery(
                fusion=models.Fusion(fusion_method.upper())
            )
            
            # Exécution de la recherche hybride
            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=prefetch,
                query=fusion,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            documents = []
            for point in results.points:
                documents.append({
                    'id': str(point.id),
                    'score': point.score,
                    'text': point.payload.get('text', ''),
                    'filename': point.payload.get('filename', ''),
                    'chunk_index': point.payload.get('chunk_index', 0),
                    'doc_id': point.payload.get('doc_id', ''),
                    'metadata': point.payload
                })
            
            logger.info(f"✅ {len(documents)} résultats trouvés (hybrid search)")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche hybride: {e}")
            return []

    
    def delete_document(self, filename: str) -> bool:
        """Supprime tous les chunks d'un document"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="filename",
                            match=models.MatchValue(value=filename)
                        )
                    ]
                )
            )
            logger.info(f"✅ Document {filename} supprimé")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur suppression: {e}")
            return False
    
    def collection_info(self) -> Dict:
        """Retourne les informations sur la collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'status': info.status,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'segments_count': info.segments_count,
                'config': {
                    'dense': info.config.params.vectors,
                    'sparse': info.config.params.sparse_vectors
                }
            }
        except Exception as e:
            logger.error(f"❌ Erreur info collection: {e}")
            return {}