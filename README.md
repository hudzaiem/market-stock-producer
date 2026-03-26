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
│   └── docker-compose.yml
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

   Create a `.env` file in the project root:

   ```env
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   KAFKA_USERNAME=your_username
   KAFKA_PASSWORD=your_password
   KAFKA_TOPIC=stock-stream
   ```

3. **Stock list**

   Place an Excel file at `seeds/stock_list.xlsx` with a `Code` column containing IDX stock codes (e.g., `BBCA`, `TLKM`). You can download the list from [IDX](https://www.idx.co.id/).

## Usage

### Local

```bash
python main.py
```

### Docker

```bash
docker compose -f deployment/docker-compose.yml up -d

# View logs
docker compose -f deployment/docker-compose.yml logs -f stock-producer

# Stop
docker compose -f deployment/docker-compose.yml down
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated broker list | `localhost:9092` |
| `KAFKA_USERNAME` | SASL username | _(empty)_ |
| `KAFKA_PASSWORD` | SASL password | _(empty)_ |
| `KAFKA_TOPIC` | Destination Kafka topic | `stock-stream` |
