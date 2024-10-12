# logger.py

import logging
from config import LOG_LEVEL, LOG_FORMAT

def setup_logger():
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    return logging.getLogger(__name__)

logger = setup_logger()
