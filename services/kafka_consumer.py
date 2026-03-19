import json
from pathlib import Path
from kafka import KafkaConsumer
from kafka.admin import NewTopic, KafkaAdminClient
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
import time, signal, sys, os

import urllib
from Retrieval.retrieval_pipeline import RetrieverPipeline
from Retrieval.vector_store import VectorStore
from services.minio_service import MinIOService
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'minio-events')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'pdf-bucket')

# Dépendances injectées (lifespan) pour éviter toute recréation
_retriever_pipeline = None
_vector_store = None


def configure_kafka_dependencies(*, retriever_pipeline=None, vector_store=None) -> None:
    global _retriever_pipeline, _vector_store
    _retriever_pipeline = retriever_pipeline
    _vector_store = vector_store

class KafkaService:
    def __init__(self):
        self.bootstrap_servers = KAFKA_BOOTSTRAP_SERVERS
        self.topic_name = KAFKA_TOPIC
        self.running = True
        self.consumer = None
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

        # Libérer la connexion Kafka si elle est déjà ouverte.
        try:
            if self.consumer is not None:
                self.consumer.close()
        except Exception:
            pass

        # Ne pas appeler sys.exit ici : permet un arrêt propre en thread.
    
    def stop(self):
        """Demande l'arrêt du consumer (safe à appeler depuis un thread)."""
        self.running = False
        try:
            if self.consumer is not None:
                self.consumer.close()
        except Exception:
            pass

    def consume_messages(self):
        """Consomme les messages avec kafka-python en boucle infinie"""
        print(f"👂 Démarrage du consumer sur {self.bootstrap_servers}...")
        
        # Attendre que Kafka soit prêt
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.consumer = KafkaConsumer(
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
        try:
            while self.running:
                try:
                    # Poll les messages avec un timeout
                    messages = self.consumer.poll(timeout_ms=5000)

                    if messages:
                        for topic_partition, records in messages.items():
                            for message in records:
                                print(
                                    f"\n📨 Message reçu (partition {message.partition}, offset {message.offset})"
                                )

                                try:
                                    event = json.loads(message.value.decode("utf-8"))
                                    print(f"   Event: {json.dumps(event, indent=2)[:200]}...")

                                    if "Records" in event and len(event["Records"]) > 0:
                                        # Nom de l'événement
                                        record = event["Records"][0]
                                        event_name = record.get("eventName", "")

                                        # Extraire le nom du fichier
                                        encoded_name = event["Records"][0]["s3"]["object"]["key"]
                                        decoded_name = urllib.parse.unquote(
                                            encoded_name.replace("+", " ")
                                        )

                                        print(f"📄 Encodé: {encoded_name}")
                                        print(f"📄 Décodé: {decoded_name}")

                                        # Détection du type d'événement
                                        if "ObjectRemoved" in event_name:
                                            print(f"🗑️ Événement de SUPPRESSION détecté: {event_name}")
                                            handle_deletion(decoded_name, record)
                                        elif "ObjectCreated" in event_name:
                                            print(
                                                f"📄 Événement de CRÉATION/MODIFICATION détecté: {event_name}"
                                            )
                                            handle_creation(decoded_name, record)
                                        else:
                                            print(f"⚠️ Type d'événement non géré: {event_name}")
                                    else:
                                        print("   ℹ Format d'event inattendu")

                                except Exception as e:
                                    print(f"   ❌ Erreur parsing: {e}")

                                print("-" * 60)
                    else:
                        # Aucun message, on continue (point si silence)
                        print(".", end="", flush=True)
                        # Sleep court pour réagir rapidement à stop()
                        time.sleep(0.5)
                except Exception as e:
                    print(f"\n❌ Erreur dans la boucle consumer: {e}")
                    time.sleep(5)
        finally:
            print("\n🛑 Consumer arrêté")
            if self.consumer:
                try:
                    self.consumer.close()
                except Exception:
                    pass
            
def handle_deletion(filename: str, record: dict):
    """Traite la suppression d'un document"""
    print(f"🗑️ Suppression du document: {filename}")
    
    try:
        vector_store = _vector_store or VectorStore()
        
        resultat = vector_store.delete_document(filename=filename)
        
        if resultat:
            print(f"✅ Document {filename} supprimé avec succès")
        else:
            print(f"❌ Échec du suppression du document '{filename}'")
    except Exception as e:
        print(f"❌ Erreur lors du traitement du document '{filename}': {e}")
        import traceback
        traceback.print_exc()
    

def handle_creation(filename: str, record: dict):
    """Traite la création/modification d'un document"""
    print(f"📄 Traitement du nouveau document: {filename}")
    
    # pipeline RAG
    try:
        # Initialisation du pipeline RAG
        pipeline = _retriever_pipeline or RetrieverPipeline()

        print(f"🔄 Traitement du document: {MINIO_BUCKET}/{filename}")

        # pipeline pour indexer les documents
        success = pipeline.process_document(MINIO_BUCKET, filename)

        if success:
            print(f"✅ Document '{filename}' traité avec succès !")
        else:
            print(f"❌ Échec du traitement du document '{filename}'")

    except Exception as e:
        print(f"❌ Erreur lors du traitement du document réel: {e}")
        import traceback
        traceback.print_exc()


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
        minio_service.setup(bucket_name=MINIO_BUCKET, topic_name=KAFKA_TOPIC)
        
        # 2️⃣ Configurer Kafka
        print("\n📋 Configuration Kafka...")
        service = KafkaService()
        
        # Attendre que Kafka soit prêt
        # print("⏳ Attente de Kafka...")
        # time.sleep(5)
        
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