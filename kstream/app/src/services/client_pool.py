import yaml
from pathlib import Path

from confluent_kafka.admin import AdminClient
from confluent_kafka.schema_registry import SchemaRegistryClient

from src.services.kafka_context.consumer_context import ConsumerContext
from src.services.kafka_context.producer_context import ProducerContext
from src.utils.metainfo import ROOT_DIR

class PoolContext:

    def __init__(
            self,
            consumers: list[ConsumerContext],
            producers: list[ProducerContext],
            schema_registry: SchemaRegistryClient,
            admin: AdminClient
    ):
        self.schema_registry = schema_registry
        self.producers = {producer.name: producer for producer in producers}
        self.consumers = {consumer.name: consumer for consumer in consumers}
        self.admin = admin

    @classmethod
    def from_yaml(cls, path: Path = ROOT_DIR / "kstream.conf.yml"):
        with open(path, 'r') as f:
            environment = yaml.safe_load(f)
        admin = AdminClient(environment["kafka"]["admin"]["config"])
        schema_registry = SchemaRegistryClient({
            "url": environment["kafka"]["schema_registry"]
        })
        consumers = environment["kafka"]["consumers"]
        producers = environment["kafka"]["producers"]
        consumer_instances = list()
        for consumer in consumers:
            consumer_instance = ConsumerContext(**consumer)
            if schema_registry:
                consumer_instance.configure(registry_client=schema_registry)
            else:
                consumer_instance.configure()
            consumer_instances.append(consumer_instance)
        producer_instances = list()
        for producer in producers:
            producer_instance = ProducerContext(**producer)
            if schema_registry:
                producer_instance.configure(registry_client=schema_registry)
            else:
                producer_instance.configure()
            producer_instances.append(producer_instance)
        return cls(
            consumers=consumer_instances,
            producers=producer_instances,
            schema_registry=schema_registry,
            admin=admin
        )
