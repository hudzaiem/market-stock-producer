import kafka
import json


class KafkaConnection:
    def __init__(self, bootstrap_servers: list[str], security_protocol: str = "SASL_PLAINTEXT", username: str = "", password: str = ""):
        self.bootstrap_servers = bootstrap_servers
        self.security_protocol = security_protocol
        self._username = username
        self._password = password

    def _sasl_kwargs(self):
        if "SASL" in self.security_protocol:
            return {
                "sasl_mechanism": "SCRAM-SHA-256",
                "sasl_plain_username": self._username,
                "sasl_plain_password": self._password,
            }
        return {}

    def create_producer(self):
        return kafka.KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            **self._sasl_kwargs(),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
        )
            
    def create_consumer(self):
        return kafka.KafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            **self._sasl_kwargs(),
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )