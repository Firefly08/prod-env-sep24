from kafka import KafkaProducer
print("KafkaProducer imported successfully")
producer = KafkaProducer(bootstrap_servers='localhost:9092')
print("Kafka producer created")