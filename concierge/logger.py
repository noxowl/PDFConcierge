import logging


def get_logger(module_name):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(module_name)
    stream = logging.StreamHandler()
    logger.addHandler(stream)
    return logger
