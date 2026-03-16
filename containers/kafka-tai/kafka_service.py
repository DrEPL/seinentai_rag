import json
from kafka import KafkaConsumer
from kafka.admin import NewTopic, KafkaAdminClient
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import time
import signal
import sys
from services.minio_service import MinIOService

class KafkaService:
    def __init__(self, bootstrap_servers="kafka-tai:9091"):
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = "minio-events"
        self.running = True
        print(f"📡 Kafka bootstrap servers: {self.bootstrap_servers}")

    def create_topics(self):
        """Crée le topic avec kafka-python"""
        print(f"🔧 Création du topic {self.topic_name}...")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
                
                # Vérifier si le topic existe
                topics = admin.list_topics()
                if self.topic_name in topics:
                    print(f"ℹ Topic {self.topic_name} existe déjà")
                    return True
                
                # Créer le topic
                topic = NewTopic(name=self.topic_name, num_partitions=3, replication_factor=1)
                admin.create_topics([topic])
                print(f"✅ Topic créé: {self.topic_name}")
                return True
                
            except NoBrokersAvailable:
                print(f"⏳ Kafka pas prêt (tentative {attempt+1}/{max_retries})...")
                time.sleep(5)
            except TopicAlreadyExistsError:
                print(f"ℹ Topic déjà existant: {self.topic_name}")
                return True
            except Exception as e:
                print(f"❌ Erreur création topic (tentative {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return False
        return False
    
    def handle_shutdown(self, signum, frame):
        """Gère l'arrêt propre du service"""
        print("\n🛑 Arrêt du service demandé...")
        self.running = False
        sys.exit(0)
    
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
    
    # Configurer les handlers de signal pour un arrêt propre
    service = None
    
    def signal_handler(sig, frame):
        if service:
            service.running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1️⃣ Configurer MinIO
        print("\n📦 Configuration de MinIO...")
        minio_service = MinIOService()
        minio_service.setup(bucket_name="pdf-bucket", topic_name="minio-events")
        
        # 2️⃣ Configurer Kafka
        print("\n📋 Configuration Kafka...")
        service = KafkaService(bootstrap_servers="kafka-tai:9091")
        
        # Attendre que Kafka soit prêt
        print("⏳ Attente de Kafka...")
        time.sleep(5)
        
        # Créer le topic
        if service.create_topics():
            # 3️⃣ Écouter les messages (boucle infinie)
            print("\n🎧 Démarrage du consumer...")
            service.consume_messages()
        else:
            print("❌ Impossible de créer le topic, abandon")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    finally:
        print("\n👋 Service terminé")