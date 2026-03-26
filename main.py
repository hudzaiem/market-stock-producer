import kafka
import logging

from dotenv import load_dotenv

from src.api.yfinance import YFinanceAPI
from src.config.kafka import KafkaConfig
from src.config.stock_list import get_stock_list
from src.connection.kafka import KafkaConnection
from src.core.stock_producer import StockProducer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    kafka_cfg = KafkaConfig()
    
    logger.info(
        "Kafka config loaded — brokers=%s, topic=%s",
        kafka_cfg.bootstrap_servers,
        kafka_cfg.topic,
    )

    kafka_conn = KafkaConnection(
        bootstrap_servers=kafka_cfg.bootstrap_servers,
        username=kafka_cfg.username,
        password=kafka_cfg.password,
    )
    producer = kafka_conn.create_producer()

    stock_producer = StockProducer(producer=producer, topic=kafka_cfg.topic)

    stock_list = get_stock_list()

    yf_api = YFinanceAPI()
    try:
        yf_api.get_stream_data(
            stock_list=stock_list,
            message_handler=stock_producer.message_handler,
        )
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down…")
    finally:
        stock_producer.close()


if __name__ == "__main__":
    main()