import datetime
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
        """
        A wrapper around confluent_kafka.schema_registry.SchemaRegistryClient.

        Contains a premade schema registry client and schema information pertaining a given topic.
        Kafka Channels will refer to this class in order to get schema information.
        If schema is not provided in the config.yml file, this class will not be instantiated.

        :param registry_client:
        :param schema_name:
        """

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
        if self.schema_type == "AVRO":
            fields = {item["name"]: item["type"] for item in self.schema_dict.get("fields")}
            # assumes only nullable single types
            # will have to change if there are multiple types of fields
            for field, f_type in fields.items():
                if isinstance(f_type, list):
                    fields[field] = f_type[0] if f_type[0] != "null" else f_type[1]
                    continue
                # datetime formats
                elif isinstance(f_type, dict):
                    fields[field] = 'datetime'
                    continue

            for field, f_type in fields.items():
                if f_type == "string":
                    fields[field] = ( str | None, ... )
                elif f_type == "float":
                    fields[field] = ( float | None, ... )
                elif f_type == "datetime":
                    fields[field] = ( datetime.datetime | None, ... )

            self.registered_model = create_model(
                f"TopicModel_{name}",
                __base__=BaseModel,
                **fields
            )
        else:
            raise