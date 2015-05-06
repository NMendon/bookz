import logging
from logging import config
from logging.handlers import RotatingFileHandler
import yaml

def setup_logging(app):
    """
    Policy: We have two handlers one is for debug and one is for INFO.
    for debug mode all the loggers are handled by StreamHandler
    For production we have rotating files for info and debug that rotate out separately
    :param app:
    :return:
    """
    debug = app.config['DEBUG']
    if not debug:
        print 'Not In debug mode!!'
        handler = RotatingFileHandler(app.config['BOOKZ_LOG_FILE'], maxBytes=1024 * 1024 * 100, backupCount=20)
        debug_file_handler = RotatingFileHandler(app.config['BOOKZ_LOG_DEBUG_FILE'], maxBytes=1024 * 1024 * 100, backupCount=10)
    else:
        print 'In debug mode!!'
        handler = logging.StreamHandler()
        debug_file_handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    debug_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(" %(name)s - %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.addHandler(debug_file_handler)
    # Also configure the log handler for the other loggers
    global_config = yaml.load(file(app.config['LOGGING_CONFIG_FILE']))
    config.dictConfig(global_config['logging'])
