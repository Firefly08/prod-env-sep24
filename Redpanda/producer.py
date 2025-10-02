from dotenv import load_dotenv
import os
import json
import time
from kafka import KafkaProducer

load_dotenv()

print("Loading environment variables from .env file")

producer = KafkaProducer(
    bootstrap_servers=os.getenv("BOOTSTRAP_SERVERS"),
    sasl_plain_username=os.getenv("SASL_USERNAME"),
    sasl_plain_password=os.getenv("SASL_PASSWORD"),
    security_protocol='SASL_SSL',
    sasl_mechanism='SCRAM-SHA-256',
    value_serializer=lambda v: v.encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
)

print("Kafka producer created")
for i in range(10):
    message = {
        "order_id": str(i+1),
        "customer_name": f"Customer {i}",
        "product": f"Product {i}",
        "quantity": i + 1,
        "price": round(i * 10.0, 2),
        "order_date": "2023-10-01",
        "order_time": "12:00:00"
    }
    producer.send('topic-demo',
                 key=message['order_id'],
                 value=json.dumps(message))
    print(f"Sent: {message}")
    time.sleep(1)

producer.flush()
producer.close()
print("Messages sent")