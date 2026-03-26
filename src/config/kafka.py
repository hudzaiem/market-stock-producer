import os
from dataclasses import dataclass, field


@dataclass
class KafkaConfig:
    bootstrap_servers: list[str] = field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(","))
    username: str = field(default_factory=lambda: os.getenv("KAFKA_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("KAFKA_PASSWORD", ""))
    topic: str = field(default_factory=lambda: os.getenv("KAFKA_TOPIC", "stock-stream"))
