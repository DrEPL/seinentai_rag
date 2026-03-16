from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig, TopicConfig


class MinIOService:
    """Service pour gérer MinIO et ses notifications Kafka"""
    
    def __init__(self, host: str = "minio-tai:9000", access_key: str = "minio", 
                 secret_key: str = "minio123", secure: bool = False):
        """Initialise la connexion à MinIO"""
        self.client = Minio(
            host,
            access_key=access_key,
            secret_key=secret_key,
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
            events=["s3:ObjectCreated:*"])
        
        notification_cfg = NotificationConfig(queue_config_list=[queue_config])
        self.client.set_bucket_notification(bucket_name, notification_cfg)
        print(f"✓ Notifications Kafka configurées pour le bucket '{bucket_name}' → topic '{topic_name}'")
    
    def setup(self, bucket_name: str = "pdf-bucket", topic_name: str = "minio-events") -> None:
        """Configure MinIO et les notifications en une seule étape"""
        self.create_bucket_if_not_exists(bucket_name)
        self.configure_kafka_notifications(bucket_name, topic_name)
        
# if __name__ == "__main__":
#     # 1️⃣ Configurer MinIO en premier
#     minio_service = MinIOService()
#     minio_service.setup(bucket_name="pdf-bucket", topic_name="minio-events")