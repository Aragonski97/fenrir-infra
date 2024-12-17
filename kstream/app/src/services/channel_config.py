from confluent_kafka import Consumer, TopicPartition, Producer, Message, KafkaError
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from structlog import get_logger, BoundLogger
import fastavro
import json
from pydantic import BaseModel, create_model
import yaml
from pathlib import Path
from abc import ABC, ABCMeta, abstractmethod

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class _ChannelRegistryMeta:

    def __init__(
            self,
            registry_client: str,
            schema_name: str
    ) -> None:

        self.registry_client = SchemaRegistryClient({"url": registry_client})
        self.schema_name = schema_name
        self.logger = get_logger()

        self.schema_latest_version = None
        self.schema_id = None
        self.schema_dict = None
        self.schema_type = None
        self.parsed_schema = None
        # we always expect a string as a key, but it can be changed here

        if not self.schema_name:
            self.logger.warning(event="Schema missing!")
        else:
            self.resolve_schema()

    def resolve_schema(self):
        self.schema_latest_version = self.registry_client.get_latest_version(self.schema_name)
        self.schema_id = self.schema_latest_version.schema_id
        self.schema_dict = json.loads(self.schema_latest_version.schema.schema_str)
        self.schema_type = self.schema_latest_version.schema.schema_type


class _ChannelSubject:

    def __init__(
            self,
            name: str,
            topic_name: str,
            registry_meta: dict | None = None,
            pydantic_schema: dict | None = None,
            partition: int | None = None
    ):
        """
        Unites the Topic, Partition and registry data into a singular class.
        I find this to be the best practice, because you almost always want
        to have your data structured with schemas stored in the registry.
        This will decide the serializer/deserializer based on schema name.

        :param topic_name: name of the topic
        :param partition: partition of the topic, defaulted at 0 (only one)
        :param registry_meta: config for _ChannelRegistryMeta
        """
        self.name = name
        self.topic_name = topic_name
        self.logger = get_logger()
        self.partition = None
        self.registry_meta = None
        self.pydantic_schema = None
        if partition:
            self.partition = partition
            self.topic_partition = TopicPartition(topic=self.topic_name, partition=self.partition)
        if registry_meta:
            self.registry_meta = _ChannelRegistryMeta(**registry_meta)
            self.key_serialization_method = StringSerializer('utf_8')
            self.value_serialization_method = None
        if pydantic_schema:
            self.registered_model = create_model(
                "RegisteredModel",
                __base__=BaseModel,
                **{key: (type(value) | None, ...) for key, value in pydantic_schema.items()}
            )

    def _configure_json_serialization(self) -> None:
        """
        Not yet implemented
        """
        self.logger.error("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_serialization(self) -> None:
        self.registry_meta.parsed_schema = fastavro.parse_schema(self.registry_meta.schema_dict)
        self.value_serialization_method = AvroSerializer(
            schema_registry_client=self.registry_meta.registry_client,
            schema_str=self.registry_meta.schema_latest_version.schema.schema_str,
            to_dict=lambda obj, ctx: self.registered_model.model_dump(obj, context=ctx)
        )
        self.logger.error(f"Avro serialization set for {self.name}")

    def _configure_protobuf_serialization(self) -> None:
        self.logger.error("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")


class Channel(ABC):
    """
    A Channel is the abstraction of any communication client with
    Apache Kafka server through confluent-kafka = "==2.6.1" library
    # https://github.com/confluentinc/confluent-kafka-python

    It is meant to be instantiated through inheritance:
        - ProducerChannel
        - ConsumerChannel
        - AdminChannel (not yet implemented)

    These contain the attributes and methods I found necessary to build the entire kafka suite
    a project might need. Like pools of producers and a way to instantiate them
    using a config file instead of always going through the trouble of coding it
    from scratch. Also, it provides much flexibility in terms of its interaction
    with Schema Registry.
    I found this necessary because I find confluent-kafka APIs to be lower level
    than I would ideally like.
    """
    __metaclass__ = ABCMeta

    name: str
    logger: BoundLogger
    subjects: dict[str, _ChannelSubject]
    topic_partitions: list[TopicPartition] | None = None
    config: dict

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def _configure_serialization(self, subject: _ChannelSubject) -> None:
        pass


class ProducerChannel(Channel):

    def __init__(
            self,
            name: str,
            subjects: dict[str, _ChannelSubject],
            config: dict,
    ) -> None:

        self.name = name
        self.subjects = subjects
        self.logger = get_logger()
        self.config = config
        self.channel = Producer(self.config)
        for subject in list(self.subjects.values()):
            if subject.registry_meta:
                self._configure_serialization(subject=subject)

    def __repr__(self):
        return f"Producer: {self.name}"

    def _configure_json_serialization(self, subject: _ChannelSubject) -> None:
        """
        Not yet implemented
        """
        self.logger.error("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_serialization(self, subject: _ChannelSubject) -> None:
        subject.registry_meta.parsed_schema = fastavro.parse_schema(subject.registry_meta.schema_dict)
        subject.value_serialization_method = AvroSerializer(
            schema_registry_client=subject.registry_meta.registry_client,
            schema_str=subject.registry_meta.schema_latest_version.schema.schema_str,
            to_dict=lambda obj, ctx: subject.registered_model.model_dump(obj, context=ctx)
        )
        self.logger.error(f"Avro serialization set for {self.name}")

    def _configure_protobuf_serialization(self, subject: _ChannelSubject) -> None:
        """
        Not yet implemented
        """
        self.logger.error("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")

    def _configure_serialization(self, subject: _ChannelSubject) -> None:
        match subject.registry_meta.schema_type:
            case "JSON":
                self._configure_json_serialization(subject=subject)
            case "AVRO":
                self._configure_avro_serialization(subject=subject)
            case "PROTOBUF":
                self._configure_protobuf_serialization(subject=subject)
            case _:
                self.logger.error(f"Schema of type {subject.registry_meta.schema_type} not recognized")
                raise ValueError(f"Schema of type {subject.registry_meta.schema_type} not recognized")

    def produce(self, key: str, value: BaseModel, subject_name: str) -> None:
        subject = self.subjects.get(subject_name, None)
        # Manually commit the offset for this partition only
        if not subject:
            self.logger.warning("Subject by that name doesn't exist")
            return
        try:
            if subject.registry_meta:
                key = subject.key_serialization_method(key, SerializationContext(subject.topic_name, MessageField.KEY)),
                value = subject.value_serialization_method(
                    value, SerializationContext(subject.topic_name, MessageField.VALUE)
                )
            else:
                key = subject.key_serialization_method(key, SerializationContext(subject.topic_name, MessageField.KEY)),
                value = value.model_dump_json(indent=True, exclude_none=True)
            # either it's all, or 0 or more
            assert subject.partition in {-1, None} or subject.partition >= 0
            self.channel.produce(
                topic=subject.topic_name,
                partition=subject.topic_partition,
                key=key,
                value=value,
                on_delivery=self.delivery_report
            )
            return
        except Exception as err:
            self.logger.warning(err)
            raise err

    def delivery_report(self, err: KafkaError, msg: Message):
        if err is not None:
            self.logger.info("Delivery failed for User record {}: {}".format(msg.key(), err))
            return
        self.logger.info('User record {} successfully produced to {} [{}] at offset {}'.format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()))


class ConsumerChannel(Channel):

    def __init__(
            self,
            name: str,
            subjects: dict[str, dict],
            config: dict,
    ) -> None:

        self.name = name
        self.logger = get_logger()
        self.subjects = {key: _ChannelSubject(**value) for key, value in subjects.items()}
        self.config = config
        self.topic_partitions = [item.topic_partition for item in list(self.subjects.values())]
        self.channel = Consumer(self.config)
        for subject in list(self.subjects.values()):
            if subject.registry_meta:
                self._configure_serialization(subject)

    def __repr__(self):
        return f"Consumer: {self.name}"
    #
    # def attach(self):
    #     for subject in self.subjects:
    #         if subject

    def _configure_json_serialization(self, subject: _ChannelSubject) -> None:
        """
        Not yet implemented
        """
        self.logger.error("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_serialization(self, subject: _ChannelSubject) -> None:
        subject.registry_meta.parsed_schema = fastavro.parse_schema(subject.registry_meta.schema_dict)
        subject.value_serialization_method = AvroDeserializer(
            schema_registry_client=subject.registry_meta.registry_client,
            schema_str=subject.registry_meta.schema_latest_version.schema.schema_str,
            from_dict=lambda obj, ctx: subject.registered_model.model_validate(obj, context=ctx)
        )
        self.logger.error(f"Avro serialization set for {self.name}")

    def _configure_protobuf_serialization(self, subject: _ChannelSubject) -> None:
        self.logger.error("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")

    def _configure_serialization(self, subject: _ChannelSubject) -> None:
        match subject.registry_meta.schema_type:
            case "JSON":
                self._configure_json_serialization(subject=subject)
            case "AVRO":
                self._configure_avro_serialization(subject=subject)
            case "PROTOBUF":
                self._configure_protobuf_serialization(subject=subject)
            case None:
                self._using_schema = False
                return
            case _:
                self.logger.error(f"Schema of type {subject.registry_meta.schema_type} not recognized")
                raise ValueError(f"Schema of type {subject.registry_meta.schema_type} not recognized")

    def _extract_message(self, msg: Message):

        self.logger.info(event="Message received.", topic=msg.topic(), partition=msg.partition())
        # expects subjects to be unique by topic and partition!!!!
        for sbj in list(self.subjects.values()):
            if sbj.topic_name == msg.topic() and sbj.partition == msg.partition():
                subject = sbj
                break
        else:
            self.logger.warning("Subject by that topic and partition combination doesn't exist!")
            return
        assert subject.partition in {-1, None} or subject.partition >= 0
        if msg.error():
            self.logger.error(
                event="While extracting the message error occured.",
                msg_error=msg.error(),
                fallback="Skipping..."
            )
            return None, None
        if self._using_schema:
            key = subject.key_serialization_method(msg.key(), SerializationContext(msg.topic(), MessageField.KEY))
            value = subject.value_serialization_method(
                msg.value(),
                SerializationContext(msg.topic(), MessageField.VALUE)
            )
            return key, value
        else:
            return msg.key(), msg.value()

    def commit(self, msg: Message):
        # Commit the offset
        tp = TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)
        self.channel.commit(offsets=[tp], asynchronous=False)

    def get_subject(self, msg: Message) -> _ChannelSubject:
        for sbj in list(self.subjects.values()):
            if sbj.topic_name == msg.topic() and sbj.partition == msg.partition():
                return sbj

    def consume(self):
        topics_for_subscription = list()
        topics_for_assignment = list()
        for subject in list(self.subjects.values()):
            if subject.partition in {-1, None}:
                topics_for_subscription.append(subject.topic_name)
            else:
                topics_for_assignment.append(subject.topic_name)
        self.channel.subscribe(topics=topics_for_subscription)
        self.channel.assign(topics_for_assignment)

        while True:
            try:
                self.logger.info(event="Requesting a message...")
                msg = self.channel.poll(3600)
                if msg is None:
                    self.logger.info(event="No new message received after an hour, polling again...")
                    continue
                self.logger.info(event="Message received.", topic=msg.topic(), partition=msg.partition())
                subject = self.get_subject(msg)
                if msg.error():
                    self.logger.error(
                        event="While extracting the message error occured.",
                        msg_error=msg.error(),
                        fallback="Skipping..."
                    )
                    return None, None
                if subject.registry_meta:
                    key = subject.key_serialization_method(
                        msg.key(),
                        SerializationContext(msg.topic(), MessageField.KEY)
                    )
                    value = subject.value_serialization_method(
                        msg.value(),
                        SerializationContext(msg.topic(), MessageField.VALUE)
                    )
                    yield key, value
                else:
                    yield msg.key(), msg.value()

            except Exception as err:
                self.logger.error(event="Consuming a message...", err=err)
                self.close()
                raise err

    def close(self):
        self.logger.info(event="Closing kafka consumer.")
        self.channel.close()  # Close consumer gracefully

    def pause(self, subject_name: str):
        subject = self.subjects.get(subject_name, None)
        self.logger.info(event=f"Pausing subject: {subject.name}")
        self.channel.pause(partitions=[subject.topic_partition])

    def resume(self, subject_name: str):
        subject = self.subjects.get(subject_name, None)
        self.logger.info(event="Resuming kafka consumer.")
        self.channel.resume(partitions=[subject.topic_partition])




class ChannelPoolModel:

    def __init__(self, consumers: list[ConsumerChannel], producers: list[ProducerChannel]):
        self.producers = {channel.name: channel for channel in producers}
        self.consumers = {channel.name: channel for channel in consumers}
        for name, channel in self._channels.items():
            setattr(self, name, channel)

    # def __len__(self):
    #     return len(self._channels)

    # to make it a real pool we need functions that will give one from the stack,
    # but this is for the later date

    def __getattr__(self, item):
        try:
            return self._channels[str(item)]
        except KeyError as err:
            raise AttributeError(f"Attribute {err.args[0]} doesn't exist for class {self.__class__.__name__}")

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._channels[key] = value
            setattr(self, key, value)
            return
        raise AttributeError(f"Attribute of type {type(key)} can't be set for class {self.__class__.__name__}")

    @classmethod
    def from_yaml(cls, path: Path = ROOT_DIR / "kstream.conf.yml"):
        """
        Default config loading method.
        :return: ChannelPool
        """
        with open(path, 'r') as f:
            environment = yaml.safe_load(f)

        consumers = environment["kafka"]["consumers"]
        producers = environment["kafka"]["producers"]

        for consumer in consumers:

            consumer_subjects = consumer["subjects"]

        for producer in producers:
            producer_subjects = producer["subjects"]

            consumer_subjects_instances = [_ChannelSubject(**subject) for subject in consumer_subjects]
            producer_subjects_instances = [_ChannelSubject(**subject) for subject in producer_subjects]

    # add custom env parsing, e.g .env, jsonl, etc.
    # @classmethod
    # def from_<format>(cls, path: str):
    #   with open(path, 'r') as f:
    #       data = <format(lib)>.<load_function(lib)>(f)
    #   return cls(<constructor params>)

