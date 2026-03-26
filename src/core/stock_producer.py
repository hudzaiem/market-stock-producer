import json
import logging
from kafka import KafkaProducer

logger = logging.getLogger(__name__)


class StockProducer:
    def __init__(self, producer: KafkaProducer, topic: str):
        self.producer = producer
        self.topic = topic

    def message_handler(self, message):
        """Callback passed to yfinance WebSocket.listen().
        
        Receives a websocket message, extracts the ticker as key,
        and produces the message to the Kafka topic.
        """
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            ticker = data.get("id", data.get("Ticker", "unknown"))

            self.producer.send(
                self.topic,
                key=str(ticker),
                value=data,
            )
            logger.info("Produced message for ticker=%s to topic=%s", ticker, self.topic)

        except Exception as e:
            logger.error("Failed to produce message: %s", e)

    def close(self):
        """Flush pending messages and close the producer."""
        self.producer.flush()
        self.producer.close()
        logger.info("Producer closed.")
