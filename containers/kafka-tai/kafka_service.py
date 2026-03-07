import json
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import time
from minio_service import MinIOService

class KafkaService:
    def __init__(self, bootstrap_servers="kafka-tai:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = "minio-events"
        print(f"📡 Kafka bootstrap servers: {self.bootstrap_servers}")

    def create_topics(self):
        """Crée le topic avec kafka-python"""
        print(f"🔧 Création du topic {self.topic_name}...")
        
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            
            # Vérifier si le topic existe
            topics = admin.list_topics()
            if self.topic_name in topics:
                print(f"ℹ Topic {self.topic_name} existe déjà")
                return
            
            # Créer le topic
            topic = NewTopic(name=self.topic_name, num_partitions=3, replication_factor=1)
            admin.create_topics([topic])
            print(f"✅ Topic créé: {self.topic_name}")
            
        except NoBrokersAvailable:
            print(f"❌ Impossible de se connecter à Kafka sur {self.bootstrap_servers}")
        except TopicAlreadyExistsError:
            print(f"ℹ Topic déjà existant: {self.topic_name}")
        except Exception as e:
            print(f"❌ Erreur création topic: {e}")
    
    def consume_messages(self):
        """Consomme les messages avec kafka-python en boucle infinie"""
        print(f"👂 Démarrage du consumer sur {self.bootstrap_servers}...")
        
        # Attendre que Kafka soit prêt
        consumer = None
        max_retries = 10
        for attempt in range(max_retries):
            try:
                consumer = KafkaConsumer(
                    self.topic_name,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    group_id="minio-consumer-group",
                    consumer_timeout_ms=1000,  # Timeout court pour pouvoir vérifier running
                    max_poll_records=10
                )
                print("✅ Consumer connecté!")
                break
            except NoBrokersAvailable:
                print(f"⏳ Kafka pas prêt (tentative {attempt+1}/{max_retries})...")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Erreur: {e}")
                time.sleep(5)
        else:
            print("❌ Impossible de se connecter à Kafka")
            return

        print("✅ Consumer démarré, écoute des messages...")
        print("Appuyez sur Ctrl+C pour arrêter")
        print("-" * 60)

        # Boucle infinie pour garder le service actif
        while self.running:
            try:
                # Poll les messages avec un timeout
                messages = consumer.poll(timeout_ms=1000)
                
                if messages:
                    for topic_partition, records in messages.items():
                        for message in records:
                            print(f"\n📨 Message reçu (partition {message.partition}, offset {message.offset})")
                            
                            try:
                                event = json.loads(message.value.decode('utf-8'))
                                print(f"   Event: {json.dumps(event, indent=2)[:200]}...")
                                
                                # Extraire le nom du fichier
                                if 'Records' in event and len(event['Records']) > 0:
                                    file_name = event['Records'][0]['s3']['object']['key']
                                    print(f"   📄 Nouveau PDF détecté : {file_name}")
                                    # Ici ton pipeline RAG
                                else:
                                    print(f"   ℹ Format d'event inattendu")
                                    
                            except Exception as e:
                                print(f"   ❌ Erreur parsing: {e}")
                            
                            print("-" * 60)
                else:
                    # Aucun message, on continue (affiche un point toutes les 10 secondes)
                    print(".", end="", flush=True)
                    
            except Exception as e:
                print(f"\n❌ Erreur dans la boucle consumer: {e}")
                time.sleep(5)

        print("\n🛑 Consumer arrêté")
        if consumer:
            consumer.close()


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
    kafka_service = KafkaService(bootstrap_servers="kafka-tai:9092")
    
    # Attendre que Kafka soit prêt
    print("⏳ Attente de Kafka...")
    time.sleep(10)
    
    # Créer le topic
    if kafka_service.create_topics():
        # 3️⃣ Écouter les messages (boucle infinie)
        print("\n🎧 Démarrage du consumer...")
        kafka_service.consume_messages()
    else:
        print("❌ Impossible de créer le topic, abandon")
    
    # 3️⃣ Écouter les messages
    print("\n🎧 Démarrage du consumer...")
    kafka_service.consume_messages()