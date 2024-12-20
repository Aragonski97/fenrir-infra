from pydantic import BaseModel, Field
from src.config.structlog_config import configure_logging
from src.utils.metainfo import ROOT_DIR
from pydantic_settings import BaseSettings
import yaml

configure_logging()

class AdminConfig(BaseModel):
    config: dict

class SchemaRegistryConfig(BaseModel):
    url: str

class TopicConfig(BaseModel):
    name: str
    partitions: list[int] | None = Field(default=None)
    schema_name: str | None = Field(default=None)

class ClientConfig(BaseModel):
    name: str
    topic: TopicConfig | None = Field(default=None)
    config: dict

class KafkaConfig(BaseModel):

    admin: AdminConfig
    schema_registry: SchemaRegistryConfig
    consumers: list[ClientConfig] | None = Field(default=None)
    producers: list[ClientConfig] | None = Field(default=None)

class AppConfiguration(BaseSettings):

    # add more fields respective of your application
    kafka: KafkaConfig


    class Config:
        case_sensitive = False
        secrets_dir = '/run/secrets'

    @classmethod
    def from_yaml(cls, path: str):
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)


app_config = AppConfiguration.from_yaml(path=ROOT_DIR /'config.yml')
