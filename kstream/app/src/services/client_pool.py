from confluent_kafka.admin import AdminClient
from confluent_kafka.schema_registry import SchemaRegistryClient
from src.services.kafka_context.consumer_context import ConsumerContext
from src.services.kafka_context.producer_context import ProducerContext
from src.config.app_config import app_config

class PoolContext:

    def __init__(self):
        self.admin: AdminClient | None = None
        self.schema_registry: SchemaRegistryClient | None = None
        self.producers: dict[ProducerContext] | None = None
        self.consumers: dict[ConsumerContext] | None = None

    def from_config(self):
        if app_config.kafka.admin:
            self.admin = AdminClient(app_config.kafka.admin.config)
        else:
            raise ValueError("Kafka admin section missing from config.")
        if app_config.kafka.schema_registry:
            self.schema_registry = SchemaRegistryClient(app_config.kafka.schema_registry.model_dump())
        else:
            raise ValueError("Kafka schema registry section missing from config.")
        consumers = list()
        producers = list()
        if app_config.kafka.consumers:
            for consumer_config in app_config.kafka.consumers:
                consumer = ConsumerContext(**consumer_config.model_dump())
                consumer.configure(registry_client=self.schema_registry)
                consumers.append(consumer)
            self.consumers = {consumer.name: consumer for consumer in consumers}
        if app_config.kafka.producers:
            for producer_config in app_config.kafka.producers:
                producer = ProducerContext(**producer_config.model_dump())
                producer.configure(registry_client=self.schema_registry)
                producers.append(producer)
            self.producers = {producer.name: producer for producer in producers}
        return

pool = PoolContext()