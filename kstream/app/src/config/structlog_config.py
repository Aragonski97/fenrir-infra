#
# inspiration https://gist.github.com/psviderski/2f06bc13017aa33630cfd752c8522cb2
#
import logging
import logging.config
import structlog
from urllib.parse import urlparse



def configure_logging():
    # This list contains all the attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    LOG_RECORD_ATTRIBUTES = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'levelname', 'levelno', 'lineno', 'message', 'module',
        'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'stack_info', 'thread', 'threadName',
    }
    BASIC_TYPES = (str, bool, int, float, type(None))

    def structlog_to_stdlib_adapter(logger, method_name, event_dict):
        """
        Pass the `event_dict` as `extra` keyword argument to the standard config.
        """
        exclude_keys = ['config', 'level']
        event = event_dict.pop('event', "")
        for key in exclude_keys:
            event_dict.pop(key, None)
        # Rename keys that conflict with the reserved LogRecord attributes
        conflicting_keys = set(event_dict) & LOG_RECORD_ATTRIBUTES
        for key in conflicting_keys:
            event_dict[key + '_'] = event_dict.pop(key)
        # Replace extra values of non-basic types with their string representation to make
        # sure they will become JSON-serializable (essential for logstash logging handler).
        event_dict = {k: v if isinstance(v, BASIC_TYPES) else repr(v)
                      for k, v in event_dict.items()}
        kwargs = {
            'extra': event_dict,
            'exc_info': 'exception' in event_dict,
        }
        return (event,), kwargs

    def extract_stdlib_extra(logger, method_name, event_dict):
        """
        Extract the `extra` key-values from the standard config record
        and populate the `event_dict` with them.
        """
        record_extra = {k: v for k, v in vars(event_dict['_record']).items()
                        if k not in LOG_RECORD_ATTRIBUTES}
        event_dict.update(record_extra)
        return event_dict

    def add_function_and_line(_, method_name, event_dict):
        if method_name in ["error", "critical", "warning"]:
            event_dict["module"] = event_dict["_record"].module
            event_dict["function"] = event_dict["_record"].funcName
            event_dict["line"] = event_dict["_record"].lineno
        return event_dict

    logging_dict = {
        "version": 1,
        'disable_existing_loggers': False,
        'formatters': {
            'colored': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(colors=True),
                'foreign_pre_chain': [
                    # Add config name, log level, timestamp and extra dict to
                    # the event_dict if the log entry is not from structlog.
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S'),
                    structlog.processors.format_exc_info,
                    add_function_and_line,
                    extract_stdlib_extra,
                ]
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            }
        },
        "loggers": {
            "": {  # configuring root config, which will be called in main.py (config = get_logger()  # get root config)
                "handlers": ["console"
                             ],
                "level": "DEBUG",
                "propagate": True,
            },
        }
    }

    logging.config.dictConfig(logging_dict)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog_to_stdlib_adapter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
