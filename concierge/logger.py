import logging


def get_logger(module_name):
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        stream = logging.StreamHandler()
        logger.addHandler(stream)
        logger.setLevel(level=logging.INFO)
    return logger
