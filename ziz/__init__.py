"""
Ziz Evaluation System

A user-experience-driven evaluation framework for AI applications that turns
user interactions into actionable insights.

The Ziz SDK provides a simple, powerful interface for logging outputs and
interactions from your AI applications for evaluation and analysis.
"""

__version__ = "0.1.0"
__author__ = "Oz Shaked"
__email__ = "oz@mozico.nl"

# Import SDK components for easy access
from .sdk import (
    AsyncClient,
    AsyncZizClient,
    Client,
    Feature,
    Interaction,
    Output,
    OutputTracker,
    RedactionManager,
    RetryManager,
    ZizClient,
    ZizConfig,
    track_function,
    track_output,
)
from .sdk.decorators.context import atrack_output

# Context manager functions
from .sdk.decorators.context import track_output as track_output_context

__all__ = [
    # Version info
    "__version__",
    # Main client classes
    "Client",
    "AsyncClient",
    "ZizClient",
    "AsyncZizClient",
    # Configuration and types
    "ZizConfig",
    "Output",
    "Interaction",
    "Feature",
    # Decorators and context managers
    "OutputTracker",
    "track_output",
    "track_function",
    "track_output_context",
    "atrack_output",
    # Utilities
    "RedactionManager",
    "RetryManager",
]
