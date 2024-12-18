import json
from confluent_kafka.schema_registry import SchemaRegistryClient
from structlog import get_logger
from pydantic import BaseModel, create_model


class RegistryContext:

    def __init__(
            self,
            registry_client: SchemaRegistryClient,
            schema_name: str
    ) -> None:

        self.registry_client = registry_client
        self.schema_name = schema_name
        self.logger = get_logger()

        self.schema_latest_version = None
        self.schema_id = None
        self.schema_dict = None
        self.schema_type = None
        self.parsed_schema = None
        self.registered_model = None

        if not self.schema_name:
            self.logger.warning(event="Schema missing!")
        else:
            self.resolve_schema()

    def resolve_schema(self):
        self.schema_latest_version = self.registry_client.get_latest_version(self.schema_name)
        self.schema_id = self.schema_latest_version.schema_id
        self.schema_dict = json.loads(self.schema_latest_version.schema.schema_str)
        self.schema_type = self.schema_latest_version.schema.schema_type

    def create_registered_model(self, name):
        self.registered_model = create_model(
            f"TopicModel_{name}",
            __base__=BaseModel,
            **{key: (type(value) | None, ...) for key, value in self.schema_dict.items()}
        )
