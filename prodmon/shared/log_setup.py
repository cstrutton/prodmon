from loguru import logger
import os
import sys


def get_logger():
    log_level = os.environ.get("LOG_LEVEL", default='INFO')

    # Remove and reconfigure default sys.error logger
    logger.remove(0)
    logger.add(sys.stderr, level=log_level)

    # configure file logger
    if os.environ.get("DEBUG", default=False):
        logger.add('templogs/prodmon-collect.log', level=log_level)
    else:
        logger.add('/var/log/prodmon-collect.log', rotation="10 Mb", level=log_level)

    logger.info(f'Logging set to {log_level}')
    return logger
