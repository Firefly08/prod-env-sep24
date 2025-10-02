from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

admin = KafkaAdminClient(
  bootstrap_servers=os.getenv("BOOTSTRAP_SERVERS"),
  sasl_plain_username=os.getenv("SASL_USERNAME"),
  sasl_plain_password=os.getenv("SASL_PASSWORD"),
  security_protocol="SASL_SSL",
  sasl_mechanism="<SCRAM-SHA-256 or SCRAM-SHA-512>",
)

try:
  topic = NewTopic(name="demo-topic", num_partitions=1, replication_factor=-1, replica_assignments=[])
  admin.create_topics(new_topics=[topic])
  print("Created topic")
except TopicAlreadyExistsError as e:
  print("Topic already exists")
finally:
  admin.close()