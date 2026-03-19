import logging
import os
from pathlib import Path

from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig
from typing import List, Dict, Any, Optional
from io import BytesIO
from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(str(_ENV_PATH))

logger = logging.getLogger(__name__)

class MinIOService:
    """Service pour gérer MinIO et ses notifications Kafka"""
    
    def __init__(self, secure: bool = False):
        """Initialise la connexion à MinIO"""
        # MinIO client
        self.client = Minio(
            os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key= os.environ.get("MINIO_ACCESS_KEY","minio"),
            secret_key= os.environ.get("MINIO_SECRET_KEY","minio123"), 
            secure=secure
        )
        print("✅ Connecté à MinIO")
    
    def create_bucket_if_not_exists(self, bucket_name: str) -> None:
        """Crée le bucket s'il n'existe pas"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' créé")
    
    def configure_kafka_notifications(self, bucket_name: str, topic_name: str = "minio-events") -> None:
        """Configure les notifications Kafka pour le bucket"""
        arn = "arn:minio:sqs::MYKAFKA:kafka"
        
        queue_config = QueueConfig(
            queue=arn,
            events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"])
        
        notification_cfg = NotificationConfig(queue_config_list=[queue_config])
        self.client.set_bucket_notification(bucket_name, notification_cfg)
        print(f"✓ Notifications Kafka configurées pour le bucket '{bucket_name}' → topic '{topic_name}'")
    
    def setup(self, bucket_name: str = "pdf-bucket", topic_name: str = "minio-events") -> None:
        """Configure MinIO et les notifications en une seule étape"""
        self.create_bucket_if_not_exists(bucket_name)
        self.configure_kafka_notifications(bucket_name, topic_name)
    
    def list_objects(self, bucket_name: str, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Liste les objets dans un bucket.
        
        Args:
            bucket_name: Nom du bucket
            prefix: Préfixe pour filtrer les objets
            recursive: Si True, liste récursivement
            
        Returns:
            Liste des objets avec métadonnées
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
            files = []
            for obj in objects:
                if obj.object_name:
                    files.append({
                        'filename': obj.object_name,
                        'size': obj.size,
                        'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                        'etag': obj.etag,
                        'content_type': obj.content_type
                    })
            return files
        except Exception as e:
            print(f"❌ Erreur listage objets: {e}")
            return []
    
    def get_object(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """
        Télécharge un objet depuis MinIO.
        
        Args:
            bucket_name: Nom du bucket
            object_name: Nom de l'objet
            
        Returns:
            Contenu de l'objet en bytes ou None si erreur
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except Exception as e:
            print(f"❌ Erreur téléchargement {object_name}: {e}")
            return None
    
    def put_object(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """
        Upload un objet vers MinIO.
        
        Args:
            bucket_name: Nom du bucket
            object_name: Nom de l'objet
            data: Données à uploader
            content_type: Type de contenu
            
        Returns:
            True si succès
        """
        try:
            data_stream = BytesIO(data)
            self.client.put_object(
                bucket_name, 
                object_name, 
                data_stream, 
                length=len(data),
                content_type=content_type
            )
            print(f"✅ Objet '{object_name}' uploadé dans '{bucket_name}'")
            return True
        except Exception as e:
            print(f"❌ Erreur upload {object_name}: {e}")
            return False
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Supprime un objet de MinIO.
        
        Args:
            bucket_name: Nom du bucket
            object_name: Nom de l'objet
            
        Returns:
            True si succès
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            print(f"✅ Objet '{object_name}' supprimé de '{bucket_name}'")
            return True
        except Exception as e:
            print(f"❌ Erreur suppression {object_name}: {e}")
            return False
    
    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Vérifie si un objet existe dans MinIO.
        
        Args:
            bucket_name: Nom du bucket
            object_name: Nom de l'objet
            
        Returns:
            True si l'objet existe
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except Exception:
            return False
    
    def get_object_metadata(self, bucket_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'un objet.
        
        Args:
            bucket_name: Nom du bucket
            object_name: Nom de l'objet
            
        Returns:
            Métadonnées de l'objet ou None si erreur
        """
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'filename': stat.object_name,
                'size': stat.size,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'content_type': stat.content_type
            }
        except Exception as e:
            print(f"❌ Erreur récupération métadonnées {object_name}: {e}")
            return None
        
# if __name__ == "__main__":
#     # 1️⃣ Configurer MinIO en premier
#     minio_service = MinIOService()
#     minio_service.setup(bucket_name="pdf-bucket", topic_name="minio-events")