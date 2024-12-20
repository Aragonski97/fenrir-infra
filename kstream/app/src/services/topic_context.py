from confluent_kafka import TopicPartition
from confluent_kafka.admin import AdminClient
from confluent_kafka.serialization import StringSerializer
from structlog import get_logger
from src.services.kafka_context.registry_context import RegistryContext


class TopicContext:

    def __init__(
            self,
            name: str,
            registry_context: RegistryContext | None = None,
            partitions: list[int] | None = None,
    ):
        self.name = name
        self.partitions = partitions

        self.registry_context = registry_context
        self._logger = get_logger()
        self.pydantic_schema = None
        self.partitions = list()

        if registry_context:
            self.key_serialization_method = None
            self.value_serialization_method = None
            self.registry_context.create_registered_model(name=self.name)
        else:
            self._logger.warning(f"No supplied schema")


    def get_partitions(self, admin_client: AdminClient):
        metadata = admin_client.list_topics(self.name, timeout=10)
        self.partitions = metadata.topic_contexts[self.name].partitions.keys()
        return self.partitions

    def get_topic_partitions(self):
        return [TopicPartition(topic=self.name, partition=partition) for partition in self.partitions]
