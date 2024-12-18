import yaml
from pathlib import Path

from confluent_kafka.admin import AdminClient
from confluent_kafka.schema_registry import SchemaRegistryClient

from src.services.kafka_context.consumer_context import ConsumerContext
from src.services.kafka_context.producer_context import ProducerContext

class PoolContext:

    def __init__(
            self,
            consumers: list[ConsumerContext],
            producers: list[ProducerContext],
            schema_registry: SchemaRegistryClient,
            admin: AdminClient,
            env: dict
    ):
        self.schema_registry = schema_registry
        self.producers = {producer.name: producer for producer in producers}
        self.consumers = {consumer.name: consumer for consumer in consumers}
        self.admin = admin
        self.env = env

    @classmethod
    def from_yaml(cls, path: Path):
        """
        Default config loading method.
        :return: ChannelPool
        """
        with open(path, 'r') as f:
            environment = yaml.safe_load(f)
        admin = AdminClient(environment["admin"]["config"])
        schema_registry = SchemaRegistryClient(environment["schema_registry"])
        consumers = environment["consumers"]
        producers = environment["producers"]
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
            admin=admin,
            env=environment
        )


