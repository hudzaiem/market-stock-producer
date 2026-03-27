# Market Stock Stream

Real-time Indonesian stock market data pipeline. Subscribes to live price updates via [yfinance](https://github.com/ranaroussi/yfinance) WebSocket and produces messages to Apache Kafka.

## Architecture

```
yfinance WebSocket → StockProducer (message_handler) → Kafka Topic
```

## Project Structure

```
├── main.py                        # Entrypoint
├── src/
│   ├── api/
│   │   └── yfinance.py            # YFinance API wrapper (history + websocket)
│   ├── config/
│   │   ├── kafka.py               # KafkaConfig dataclass (reads env vars)
│   │   └── stock_list.py          # Loads stock tickers from Excel
│   ├── connection/
│   │   └── kafka.py               # KafkaConnection (producer/consumer factory)
│   └── core/
│       └── stock_producer.py      # StockProducer with Kafka message handler
├── seeds/
│   └── stock_list.xlsx            # IDX stock ticker list
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml         # Base compose (works for all scenarios)
│   └── docker-compose.local.yml   # Network overlay for same-VM Kafka
├── .env                           # Local dev config (gitignored)
├── .env.docker                    # Docker same-VM config (gitignored)
├── .env.example                   # Template reference
└── requirements.txt
```

## Prerequisites

- Python 3.10+
- Apache Kafka cluster with SASL/SCRAM-SHA-256 authentication

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Copy the example and fill in your values:

   ```bash
   cp .env.example .env
   ```

3. **Stock list**

   Place an Excel file at `seeds/stock_list.xlsx` with a `Code` column containing IDX stock codes (e.g., `BBCA`, `TLKM`). You can download the list from [IDX](https://www.idx.co.id/).

## Usage

### Local Development

```bash
python main.py
```

Uses `.env` with `localhost` bootstrap servers and `SASL_PLAINTEXT`.

### Docker — Same VM as Kafka

When Kafka runs on the same machine (shared Docker network):

```bash
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.local.yml up -d
```

Uses `.env.docker` which connects via Kafka's internal PLAINTEXT listener (`kafka-1:29092`).

### Docker — Remote Kafka

When Kafka runs on a separate server:

```bash
ENV_FILE=.env.remote docker compose -f deployment/docker-compose.yml up -d
```

Uses `.env.remote` which connects via Kafka's external SASL listener (`<remote-ip>:9092`).

### Common Commands

```bash
# View logs
docker compose -f deployment/docker-compose.yml logs -f stock-producer

# Stop & remove
docker compose -f deployment/docker-compose.yml down
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated broker list | `localhost:9092` |
| `KAFKA_SECURITY_PROTOCOL` | `PLAINTEXT` or `SASL_PLAINTEXT` | `SASL_PLAINTEXT` |
| `KAFKA_USERNAME` | SASL username (only for `SASL_PLAINTEXT`) | _(empty)_ |
| `KAFKA_PASSWORD` | SASL password (only for `SASL_PLAINTEXT`) | _(empty)_ |
| `KAFKA_TOPIC` | Destination Kafka topic | `stock-stream` |
| `KAFKA_DOCKER_NETWORK` | External Docker network name (same-VM only) | — |

## Environment File Reference

| File | Purpose | Bootstrap | Protocol |
|---|---|---|---|
| `.env` | Local `python main.py` | `localhost:9092,...` | `SASL_PLAINTEXT` |
| `.env.docker` | Docker, Kafka on same VM | `kafka-1:29092,...` | `PLAINTEXT` |
| `.env.remote` | Docker, remote Kafka | `<ip>:9092,...` | `SASL_PLAINTEXT` |
