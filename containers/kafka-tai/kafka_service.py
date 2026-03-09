import json
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import time
from minio_service import MinIOService

class KafkaService:
    def __init__(self, bootstrap_servers="kafka-tai:9091"):
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = "minio-events"
        print(f"📡 Kafka bootstrap servers: {self.bootstrap_servers}")
        
    def wait_for_kafka(self):
        while True:
            try:
                admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
                admin.list_topics()
                print("✅ Kafka est prêt")
                break
            except Exception:
                print("⏳ Kafka pas prêt...")
                time.sleep(5)

    def create_topics(self):
        """Crée le topic avec kafka-python"""
        print(f"🔧 Création du topic {self.topic_name}...")
        
        try:
            print("KafkaAdminClient")
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            
            # Vérifier si le topic existe
            print("demande liste topic")
            topics = admin.list_topics()
            print("liste topic trouvé")
            if self.topic_name in topics:
                print(f"ℹ Topic {self.topic_name} existe déjà")
                return
            
            # Créer le topic
            print("demande créer topic")
            topic = [NewTopic(name=self.topic_name, num_partitions=3, replication_factor=1)]
            admin.create_topics(new_topics=topic, validate_only=False)
            print(f"✅ Topic créé: {self.topic_name}")
            
        except NoBrokersAvailable:
            print(f"❌ Impossible de se connecter à Kafka sur {self.bootstrap_servers}")
        except TopicAlreadyExistsError:
            print(f"ℹ Topic déjà existant: {self.topic_name}")
        except Exception as e:
            print(f"❌ Erreur création topic: {e}")
    
    def consume_messages(self):
        """Consomme les messages avec kafka-python"""
        print(f"👂 Démarrage du consumer sur {self.bootstrap_servers}...")
        
        # Attendre que Kafka soit prêt
        while True:
            try:
                consumer = KafkaConsumer(
                    self.topic_name,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    group_id="minio-consumer-group",
                    consumer_timeout_ms=10000
                )
                print("✅ Consumer connecté!")
                break
            except NoBrokersAvailable:
                print("⏳ Kafka pas prêt, nouvelle tentative dans 5s...")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erreur: {e}")
                time.sleep(5)

        print("✅ Consumer démarré, écoute des messages...")
        print("-" * 50)
        
        for message in consumer:
            print(f"\n📨 Message reçu (partition {message.partition}, offset {message.offset})")
            
            try:
                event = json.loads(message.value.decode('utf-8'))
                file_name = event['Records'][0]['s3']['object']['key']
                print(f"📄 Nouveau PDF détecté : {file_name}")
                # Ici ton pipeline RAG
            except Exception as e:
                print(f"❌ Erreur traitement: {e}")
            
            print("-" * 50)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 DÉMARRAGE DU SERVICE KAFKA-MINIO")
    print("=" * 60)
    
    # 1️⃣ Configurer MinIO
    print("\n📦 Configuration de MinIO...")
    minio_service = MinIOService()
    minio_service.setup(bucket_name="pdf-bucket", topic_name="minio-events")
    
    # 2️⃣ Configurer Kafka
    print("\n📋 Configuration Kafka...")
    kafka_service = KafkaService(bootstrap_servers="kafka-tai:9091")
    
    # Attendre que Kafka soit prêt
    print("⏳ Attente de Kafka...")
    time.sleep(10)
    # kafka_service.wait_for_kafka()
    
    # Créer le topic
    kafka_service.create_topics()
    
    # 3️⃣ Écouter les messages
    print("\n🎧 Démarrage du consumer...")
    kafka_service.consume_messages()