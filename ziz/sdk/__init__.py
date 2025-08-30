"""
Ziz SDK - User-experience-driven evaluation framework for AI applications.

The Ziz SDK provides a simple, powerful interface for logging outputs and
interactions from your AI applications for evaluation and analysis.

Quick Start:
    import ziz

    # Initialize client
    client = ziz.Client(api_key="your-api-key", feature_id="chatbot-v1")

    # Log an output
    output_id = client.log_output("Model response here", metadata={"model": "gpt-4"})

    # Log user feedback
    client.log_interaction("feedback", "thumbs_up", output_id=output_id)

Features:
    - Automatic batching and retry logic
    - Privacy-first with configurable redaction
    - Sync and async support
    - Context managers and decorators
    - Comprehensive error handling
    - Idempotency support
"""

from .client import AsyncZizClient, BatchManager, ZizClient
from .decorators import OutputTracker, track_function, track_output
from .types import Feature, Interaction, Output, ZizConfig
from .utils import RedactionManager, RetryManager

# Convenience alias for the main client
Client = ZizClient
AsyncClient = AsyncZizClient

# Version
__version__ = "1.0.0"

__all__ = [
    # Main client classes
    "Client",
    "ZizClient",
    "AsyncClient",
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
    # Utilities
    "RedactionManager",
    "RetryManager",
    "BatchManager",
    # Version
    "__version__",
]
