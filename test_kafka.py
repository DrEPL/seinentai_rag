from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import time

# Configuration
BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC = 'test-topic'
GROUP_ID = f'test-group-{int(time.time())}'  # Group ID unique à chaque exécution

print(f"🚀 Test Kafka avec group_id: {GROUP_ID}")

# 1️⃣ Supprimer l'ancien consumer group et recréer le topic proprement
print("\n1. Préparation du topic...")
admin_client = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)

# Supprimer l'ancien topic s'il existe (optionnel)
try:
    admin_client.delete_topics([TOPIC])
    print(f"   Ancien topic {TOPIC} supprimé")
    time.sleep(2)  # Attendre la suppression
except Exception as e:
    print(f"   Pas de topic à supprimer ou erreur: {e}")

# Créer un nouveau topic
try:
    topic_list = [NewTopic(name=TOPIC, num_partitions=3, replication_factor=1)]
    admin_client.create_topics(new_topics=topic_list, validate_only=False)
    print(f"   ✅ Topic {TOPIC} créé avec 3 partitions")
    time.sleep(2)  # Attendre la création
except TopicAlreadyExistsError:
    print(f"   ℹ Topic {TOPIC} existe déjà")
except Exception as e:
    print(f"   ❌ Erreur création topic: {e}")

# 2️⃣ Producer
print("\n2. Envoi des messages...")
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: v.encode('utf-8')
)

# Envoyer 3 messages et vérifier leur réception
for i in range(3):
    future = producer.send(TOPIC, f"Message de test {i}")
    record_metadata = future.get(timeout=10)
    print(f"   ✅ Envoyé: Message {i} (partition {record_metadata.partition}, offset {record_metadata.offset})")
    time.sleep(0.5)

producer.flush()
print("   Tous les messages envoyés")

# 3️⃣ Attendre que Kafka indexe
print("\n3. Attente de l'indexation...")
time.sleep(3)

# 4️⃣ Consumer avec configuration robuste
print("\n4. Démarrage du consumer...")
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id=GROUP_ID,
    consumer_timeout_ms=15000,  # Timeout après 15 secondes
    max_poll_records=10,
    session_timeout_ms=30000,
    heartbeat_interval_ms=10000
)

print("   Écoute en cours (15 secondes max)...")
print("-" * 50)

messages_recus = []
for message in consumer:
    value = message.value.decode('utf-8')
    print(f"   📥 Reçu: {value} (partition {message.partition}, offset {message.offset})")
    messages_recus.append(value)

consumer.close()

# 5️⃣ Bilan
print("-" * 50)
if messages_recus:
    print(f"\n✅ SUCCÈS: {len(messages_recus)} messages reçus")
    for msg in messages_recus:
        print(f"   - {msg}")
else:
    print(f"\n❌ ÉCHEC: Aucun message reçu")

    # Diagnostic avancé
    print("\n🔍 DIAGNOSTIC:")
    
    # Vérifier les topics disponibles
    try:
        topics = admin_client.list_topics()
        print(f"   Topics disponibles: {topics}")
    except:
        pass
    
    # Vérifier les consumers groups
    try:
        groups = admin_client.list_consumer_groups()
        print(f"   Consumer groups: {groups}")
    except:
        pass

admin_client.close()