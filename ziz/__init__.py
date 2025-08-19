"""
Ziz Evaluation System

A user-experience-driven evaluation framework for AI applications that turns
user interactions into actionable insights.
"""

__version__ = "0.1.0"
__author__ = "Oz Shaked"
__email__ = "oz@mozico.nl"

from ziz.sdk import ZizClient
from ziz.core.config import Config

__all__ = ["ZizClient", "Config"]