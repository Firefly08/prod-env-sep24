# Kafka Lab with Confluent Cloud (Codespaces Compatible)

This project connects to a hosted Kafka cluster on **Confluent Cloud** using `kafka-python`.

## 🌐 Confluent Cloud Setup

1. Go to [https://confluent.cloud](https://confluent.cloud) and sign up for a free account.
2. Create a **Basic cluster** and a Kafka **topic** (e.g., `group-topic`).
3. Go to **Clients > Python** to get your credentials:
   - Bootstrap server
   - API Key
   - API Secret

---

## 🛠 Codespaces Setup

1. Fork this repo and open it in **GitHub Codespaces**.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Paste your Confluent credentials into the `.env` file.

---

## 🧪 Run the Kafka Notebook

1. Open `notebooks/kafka_confluent_demo.ipynb` in Jupyter.
2. Run each cell to:
   - Connect to your Confluent Kafka topic
   - Send a message
   - Read it back from the topic

---

## ✅ Example .env File

```
BOOTSTRAP_SERVERS=pkc-xxxxx.region.gcp.confluent.cloud:9092
SASL_USERNAME=your_api_key
SASL_PASSWORD=your_api_secret
TOPIC_NAME=group-topic
```

---

## 🧰 Dependencies

These are installed automatically in Codespaces:

- `kafka-python`
- `python-dotenv`
- `jupyter`

To install locally:

```bash
pip install kafka-python python-dotenv jupyter
```