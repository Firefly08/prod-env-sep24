from kafka import KafkaConsumer

consumer = KafkaConsumer(
  bootstrap_servers=os.getenv("BOOTSTRAP_SERVERS"),
  sasl_plain_username=os.getenv("SASL_USERNAME"),
  sasl_plain_password=os.getenv("SASL_PASSWORD"),
  security_protocol="SASL_SSL",
  sasl_mechanism="<SCRAM-SHA-256 or SCRAM-SHA-512>",
  auto_offset_reset="earliest",
  enable_auto_commit=False,
  consumer_timeout_ms=10000
)
consumer.subscribe("demo-topic")

for message in consumer:
  topic_info = f"topic: {message.topic} ({message.partition}|{message.offset})"
  message_info = f"key: {message.key}, {message.value}"
  print(f"{topic_info}, {message_info}")