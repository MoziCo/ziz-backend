"""
Base client implementation for the Ziz SDK.

Contains shared functionality for both sync and async clients.
"""

import atexit
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..types import Interaction, Output, ZizConfig
from ..utils import RedactionManager, get_logger

logger = get_logger("client")


class BaseClient(ABC):
    """Base class for Ziz SDK clients."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        feature_id: Optional[str] = None,
        config: Optional[ZizConfig] = None,
        **kwargs,
    ):
        """
        Initialize the base client.

        Args:
            api_key: API key for authentication
            api_url: Base URL for the Ziz API
            feature_id: Default feature ID for operations
            config: Pre-configured ZizConfig object
            **kwargs: Additional configuration options
        """
        if config:
            self.config = config
        else:
            # Create config from environment and override with provided values
            config_overrides = {}
            if api_key:
                config_overrides["api_key"] = api_key
            if api_url:
                config_overrides["api_url"] = api_url
            if feature_id:
                config_overrides["feature_id"] = feature_id
            config_overrides.update(kwargs)

            self.config = ZizConfig.from_env(**config_overrides)

        if not self.config.api_key:
            raise ValueError(
                "API key is required. Provide it via api_key parameter "
                "or ZIZ_API_KEY environment variable."
            )

        # Initialize redaction manager
        self.redaction_manager = RedactionManager(
            enabled=not self.config.allow_content,
            redact_all_content=not self.config.allow_content,
        )

        # Track the last output ID for convenience methods
        self._last_output_id: Optional[str] = None

        logger.info(f"Initialized Ziz client with API URL: {self.config.api_url}")

        # Register cleanup on exit
        atexit.register(self.cleanup)

    @property
    def last_output_id(self) -> Optional[str]:
        """Get the ID of the last logged output."""
        return self._last_output_id

    def _prepare_output(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Output:
        """
        Prepare an Output object for logging.

        Args:
            content: The output content
            feature_id: Feature ID (uses default if not provided)
            output_id: Specific output ID (auto-generated if not provided)
            metadata: Additional metadata
            **kwargs: Additional fields for the Output

        Returns:
            Prepared Output object
        """
        if not feature_id and not self.config.feature_id:
            raise ValueError(
                "feature_id is required. Provide it directly or set a default "
                "feature_id in the client configuration."
            )

        final_feature_id = feature_id or self.config.feature_id
        final_metadata = metadata or {}

        # Apply redaction to content if needed
        redacted_content = self.redaction_manager.redact_content(
            content, allow_content=self.config.allow_content
        )

        # Apply redaction to metadata
        redacted_metadata = self.redaction_manager.redact_dict(final_metadata)

        output = Output(
            output_id=output_id,
            feature_id=final_feature_id,
            content=redacted_content,
            metadata=redacted_metadata,
            **kwargs,
        )

        return output

    def _prepare_interaction(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Interaction:
        """
        Prepare an Interaction object for logging.

        Args:
            type: Type of interaction
            value: Interaction value
            output_id: Output ID to link to (uses last output if not provided)
            interaction_id: Specific interaction ID (auto-generated if not provided)
            metadata: Additional metadata
            **kwargs: Additional fields for the Interaction

        Returns:
            Prepared Interaction object
        """
        if not output_id and not self._last_output_id:
            raise ValueError(
                "output_id is required. Provide it directly or log an output first."
            )

        final_output_id = output_id or self._last_output_id
        final_metadata = metadata or {}

        # Apply redaction to value if needed
        redacted_value = self.redaction_manager.redact_content(
            value, allow_content=self.config.allow_content
        )

        # Apply redaction to metadata
        redacted_metadata = self.redaction_manager.redact_dict(final_metadata)

        interaction = Interaction(
            interaction_id=interaction_id,
            output_id=final_output_id,
            type=type,
            value=redacted_value,
            metadata=redacted_metadata,
            **kwargs,
        )

        return interaction

    def _handle_error(self, error: Exception, operation: str) -> None:
        """
        Handle errors based on client configuration.

        Args:
            error: The error that occurred
            operation: Description of the operation that failed
        """
        logger.error(f"Error during {operation}: {error}")

        if self.config.strict_mode:
            raise error

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources. Implemented by subclasses."""
        pass

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    def log_output(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """Log an output. Returns output_id if successful."""
        pass

    @abstractmethod
    def log_interaction(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """Log an interaction. Returns interaction_id if successful."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any pending events."""
        pass
