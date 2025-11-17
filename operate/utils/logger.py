"""Logging configuration"""
from loguru import logger
import sys

def setup_logger(verbose=False):
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level)
    return logger
