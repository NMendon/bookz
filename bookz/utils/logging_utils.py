from logging import config as logging_config
import yaml

def setup_logging(default_logger='bookz/config/logging.yml'):
    """
    Calling this method from any module will configure loggers using the python logging
    infrastructure. please see resources/logging.yaml for details of the handlers.
    """
    with open(default_logger) as f:
        logging_config.dictConfig(yaml.load(f))