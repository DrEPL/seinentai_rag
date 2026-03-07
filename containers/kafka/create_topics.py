from confluent_kafka.admin import AdminClient, NewTopic
from kafka import KafkaConsumer
import time

class KafkaService:
    def __init__(self, bootstrap_servers="kafka:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = "minio-events"

    def create_topics(self):
        admin = AdminClient({"bootstrap.servers": self.bootstrap_servers})
        topic = NewTopic(self.topic_name, num_partitions=3, replication_factor=1)
        fs = admin.create_topics([topic])
        for topic, f in fs.items():
            try:
                f.result()
                print(f"✅ Topic créé: {topic}")
            except Exception as e:
                print(f"❌ Erreur création topic: {e}")

    def consume_messages(self):
        consumer = KafkaConsumer(
            self.topic_name,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="minio-consumer-group"
        )
        print("✅ Consumer démarré, écoute des messages...")
        for message in consumer:
            print("📨 Nouveau message:", message.value.decode())

if __name__ == "__main__":
    service = KafkaService()
    service.create_topics()
    service.consume_messages()  # boucle infinie