import logging
from logging.handlers import RotatingFileHandler
import yaml

def setup_logging(app):
    file_handler = RotatingFileHandler(app.config['BOOKZ_LOG_FILE'], maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(" %(name)s - %(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    global_config = yaml.load(file(
        'bookz/config/logging_prod.yml') if app.config['DEBUG'] == 'False' else file('bookz/config/logging_dev.yml'))
    logging.config.dictConfig(global_config['logging'])
