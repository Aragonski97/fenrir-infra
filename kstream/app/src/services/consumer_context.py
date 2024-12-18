import fastavro
from structlog import get_logger

from confluent_kafka import Consumer, TopicPartition, Message
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient

from src.services.kafka_context.topic_context import TopicContext
from src.services.kafka_context.registry_context import RegistryContext


class ConsumerContext:

    def __init__(
            self,
            name: str,
            topic: dict,
            config: dict
    ) -> None:

        self._logger = get_logger()
        self.name = name
        self.topic: TopicContext | None = None
        self._topic_config = topic
        self._config = config
        self._consumer = Consumer(self._config)

    def configure(
            self,
            registry_client: SchemaRegistryClient | None = None
    ):
        self._resolve_topic(registry_client)
        self._resolve_subscription()

    def _resolve_topic(
            self,
            registry_client: SchemaRegistryClient | None = None
    ):
        if registry_client:
            registry_context = RegistryContext(
                registry_client=registry_client,
                schema_name=self._topic_config["schema_name"]
            )
            self.topic = TopicContext(
                name=self._topic_config["name"],
                partitions=self._topic_config["partitions"],
                registry_context = registry_context
            )
            self._configure_serialization()
            return
        self.topic = TopicContext(
            name=self._topic_config["name"],
            partitions=self._topic_config["partitions"]
        )
        return

    def _resolve_subscription(self):
        assert self.topic
        if self.topic.partitions:
            self._consumer.assign([
                TopicPartition(topic=self.topic.name, partition=partition)
                for partition in self.topic.partitions
            ])
        else:
            self._consumer.subscribe(topics=[self.topic.name])

    def _configure_json_serialization(self) -> None:
        """
        Not yet implemented
        """
        self._logger.error("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_serialization(self) -> None:
        self.topic.registry_context.parsed_schema = fastavro.parse_schema(self.topic.registry_context.schema_dict)
        self.topic.value_serialization_method = AvroDeserializer(
            schema_registry_client=self.topic.registry_context.registry_client,
            schema_str=self.topic.registry_context.schema_latest_version.schema.schema_str,
            from_dict=lambda obj, ctx: self.topic.registry_context.registered_model.model_validate(obj, context=ctx)
        )
        self._logger.error(f"Avro serialization set for {self.name}")

    def _configure_protobuf_serialization(self) -> None:
        self._logger.error("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")

    def _configure_serialization(self) -> None:
        if not self.topic.registry_context:
            return
        match self.topic.registry_context.schema_type:
            case "JSON":
                self._configure_json_serialization()
            case "AVRO":
                self._configure_avro_serialization()
            case "PROTOBUF":
                self._configure_protobuf_serialization()
            case _:
                self._logger.error(f"Schema of type {self.topic.registry_context.schema_type} not recognized")
                raise ValueError(f"Schema of type {self.topic.registry_context.schema_type} not recognized")

    def _extract_message(
            self,
            msg: Message
    ):
        self._logger.info(event="Message received.", topic=msg.topic(), partition=msg.partition())
        if msg.error():
            self._logger.error(
                event="While extracting the message error occured.",
                msg_error=msg.error(),
                fallback="Skipping..."
            )
            return None, None
        if self.topic.registry_context:
            key = self.topic.key_serialization_method(msg.key(), SerializationContext(msg.topic(), MessageField.KEY))
            value = self.topic.value_serialization_method(
                msg.value(),
                SerializationContext(msg.topic(), MessageField.VALUE)
            )
            return key, value
        else:
            return msg.key(), msg.value()

    def commit(self, msg: Message):
        # Commit the offset
        tp = TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)
        self._consumer.commit(offsets=[tp], asynchronous=False)

    def consume(self):
        while True:
            try:
                self._logger.info(event="Requesting a message...")
                msg = self._consumer.poll(3600)
                if msg is None:
                    self._logger.info(event="No new message received after an hour, polling again...")
                    continue
                self._logger.info(event="Message received.", topic=msg.topic(), partition=msg.partition())
                if msg.error():
                    self._logger.error(
                        event="While extracting the message error occured.",
                        msg_error=msg.error(),
                        fallback="Skipping..."
                    )
                    return None, None
                if self.topic.registry_context.registry_client:
                    key = self.topic.key_serialization_method(
                        msg.key(),
                        SerializationContext(msg.topic(), MessageField.KEY)
                    )
                    value = self.topic.value_serialization_method(
                        msg.value(),
                        SerializationContext(msg.topic(), MessageField.VALUE)
                    )
                    yield key, value
                else:
                    yield msg.key(), msg.value()

            except Exception as err:
                self._logger.error(event="Consuming a message...", err=err)
                self.close()
                raise err

    def close(self):
        self._logger.info(event=f"Closing consumer: {self.name}")
        self._consumer.close()  # Close consumer gracefully

    def pause(self):
        self._logger.info(event=f"Pausing consumer: {self.name}")
        self._consumer.pause(partitions=self.topic.partitions)

    def resume(self, subject_name: str):
        self._logger.info(event="Resuming consumer: {self.name}")
        self._consumer.resume(partitions=self.topic.partitions)
