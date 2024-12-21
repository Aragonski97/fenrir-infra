from src.config.structlog_config import configure_logging
from src.services.kafka_context.client_pool import pool

# configure logging and load PoolContext

configure_logging()
pool.from_config()

