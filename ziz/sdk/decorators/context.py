"""
Context managers for the Ziz SDK.

Provides easy-to-use context managers for tracking outputs and interactions.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, List, Optional

from ..client.base import BaseClient
from ..utils import get_logger

logger = get_logger("context")


class OutputTracker:
    """Context manager for tracking output and related interactions."""

    def __init__(
        self,
        client: BaseClient,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_log: bool = True,
    ):
        """
        Initialize output tracker.

        Args:
            client: Ziz client instance
            feature_id: Feature ID (uses client default if not provided)
            output_id: Specific output ID (auto-generated if not provided)
            metadata: Initial metadata for the output
            auto_log: Whether to automatically log the output on exit
        """
        self.client = client
        self.feature_id = feature_id
        self.output_id = output_id
        self.metadata = metadata or {}
        self.auto_log = auto_log

        self._content: Any = None
        self._interactions: List[Dict[str, Any]] = []
        self._logged_output_id: Optional[str] = None

    def set_content(self, content: Any) -> None:
        """Set the output content."""
        self._content = content

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the output."""
        self.metadata[key] = value

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update output metadata."""
        self.metadata.update(metadata)

    def add_interaction(
        self,
        type: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        interaction_id: Optional[str] = None,
    ) -> None:
        """
        Add an interaction to be logged.

        Args:
            type: Type of interaction
            value: Interaction value
            metadata: Interaction metadata
            interaction_id: Specific interaction ID
        """
        interaction = {
            "type": type,
            "value": value,
            "metadata": metadata or {},
            "interaction_id": interaction_id,
        }
        self._interactions.append(interaction)

    def feedback(self, value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add feedback interaction."""
        self.add_interaction("feedback", value, metadata)

    def thumbs_up(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add thumbs up feedback."""
        self.feedback("thumbs_up", metadata)

    def thumbs_down(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add thumbs down feedback."""
        self.feedback("thumbs_down", metadata)

    def edit(
        self, edited_content: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add edit interaction."""
        self.add_interaction("edit", edited_content, metadata)

    def custom(
        self, type: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add custom interaction."""
        self.add_interaction(type, value, metadata)

    def log_output(self) -> Optional[str]:
        """Manually log the output."""
        if self._content is None:
            logger.warning("No content set for output")
            return None

        self._logged_output_id = self.client.log_output(
            content=self._content,
            feature_id=self.feature_id,
            output_id=self.output_id,
            metadata=self.metadata,
        )

        if self._logged_output_id:
            logger.debug(f"Logged output {self._logged_output_id}")

        return self._logged_output_id

    def log_interactions(self) -> List[Optional[str]]:
        """Log all accumulated interactions."""
        if not self._logged_output_id:
            logger.warning("Cannot log interactions without output ID")
            return []

        interaction_ids = []
        for interaction in self._interactions:
            interaction_id = self.client.log_interaction(
                type=interaction["type"],
                value=interaction["value"],
                output_id=self._logged_output_id,
                metadata=interaction["metadata"],
                interaction_id=interaction.get("interaction_id"),
            )
            interaction_ids.append(interaction_id)

            if interaction_id:
                logger.debug(f"Logged interaction {interaction_id}")

        return interaction_ids

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.auto_log and self._content is not None:
            self.log_output()
            self.log_interactions()

        # Don't suppress exceptions
        return False


class AsyncOutputTracker(OutputTracker):
    """Async version of OutputTracker."""

    async def log_output(self) -> Optional[str]:
        """Asynchronously log the output."""
        if self._content is None:
            logger.warning("No content set for output")
            return None

        # Check if client has async log_output method
        if hasattr(self.client, "log_output") and callable(self.client.log_output):
            if hasattr(self.client.log_output, "__await__"):
                # Async method
                self._logged_output_id = await self.client.log_output(
                    content=self._content,
                    feature_id=self.feature_id,
                    output_id=self.output_id,
                    metadata=self.metadata,
                )
            else:
                # Sync method
                self._logged_output_id = self.client.log_output(
                    content=self._content,
                    feature_id=self.feature_id,
                    output_id=self.output_id,
                    metadata=self.metadata,
                )

        if self._logged_output_id:
            logger.debug(f"Logged output {self._logged_output_id}")

        return self._logged_output_id

    async def log_interactions(self) -> List[Optional[str]]:
        """Asynchronously log all accumulated interactions."""
        if not self._logged_output_id:
            logger.warning("Cannot log interactions without output ID")
            return []

        interaction_ids = []
        for interaction in self._interactions:
            # Check if client has async log_interaction method
            if hasattr(self.client, "log_interaction") and callable(
                self.client.log_interaction
            ):
                if hasattr(self.client.log_interaction, "__await__"):
                    # Async method
                    interaction_id = await self.client.log_interaction(
                        type=interaction["type"],
                        value=interaction["value"],
                        output_id=self._logged_output_id,
                        metadata=interaction["metadata"],
                        interaction_id=interaction.get("interaction_id"),
                    )
                else:
                    # Sync method
                    interaction_id = self.client.log_interaction(
                        type=interaction["type"],
                        value=interaction["value"],
                        output_id=self._logged_output_id,
                        metadata=interaction["metadata"],
                        interaction_id=interaction.get("interaction_id"),
                    )
            else:
                interaction_id = None

            interaction_ids.append(interaction_id)

            if interaction_id:
                logger.debug(f"Logged interaction {interaction_id}")

        return interaction_ids

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.auto_log and self._content is not None:
            await self.log_output()
            await self.log_interactions()

        # Don't suppress exceptions
        return False


# Convenience functions for creating context managers


@contextmanager
def track_output(
    client: BaseClient,
    feature_id: Optional[str] = None,
    output_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    auto_log: bool = True,
):
    """
    Context manager for tracking an output.

    Usage:
        with track_output(client, metadata={"model": "gpt-4"}) as tracker:
            result = run_model()
            tracker.set_content(result)
            tracker.thumbs_up()
    """
    tracker = OutputTracker(
        client=client,
        feature_id=feature_id,
        output_id=output_id,
        metadata=metadata,
        auto_log=auto_log,
    )

    with tracker as t:
        yield t


@asynccontextmanager
async def atrack_output(
    client: BaseClient,
    feature_id: Optional[str] = None,
    output_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    auto_log: bool = True,
):
    """
    Async context manager for tracking an output.

    Usage:
        async with atrack_output(client, metadata={"model": "gpt-4"}) as tracker:
            result = await run_model_async()
            tracker.set_content(result)
            tracker.thumbs_up()
    """
    tracker = AsyncOutputTracker(
        client=client,
        feature_id=feature_id,
        output_id=output_id,
        metadata=metadata,
        auto_log=auto_log,
    )

    async with tracker as t:
        yield t
