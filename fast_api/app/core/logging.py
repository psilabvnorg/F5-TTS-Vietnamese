"""
Logging configuration
"""

import logging
import sys
from app.core.config import settings


def setup_logging():
    """
    Configure application logging
    """
    # Create logger
    logger = logging.getLogger("f5tts")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(console_handler)
    
    return logger


# Create logger instance
logger = setup_logging()
