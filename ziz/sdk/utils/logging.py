"""
Logging utilities for the Ziz SDK.

Provides consistent logging configuration across the SDK.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for the SDK with consistent formatting.

    Args:
        name: Logger name
        level: Optional log level override

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"ziz.{name}")

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    elif not logger.level:
        logger.setLevel(logging.INFO)

    return logger
