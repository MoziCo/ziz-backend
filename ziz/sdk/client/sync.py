"""
Synchronous Ziz SDK client implementation.

Provides a synchronous interface for logging outputs and interactions.
"""

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from ..types import BatchRequest, ZizResponse
from ..utils import RetryManager, get_logger
from .base import BaseClient
from .batch import BatchManager

logger = get_logger("sync_client")


class ZizClient(BaseClient):
    """Synchronous client for the Ziz API."""

    def __init__(self, **kwargs):
        """Initialize the synchronous client."""
        super().__init__(**kwargs)

        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ziz-python-sdk/1.0.0",
        })

        # Initialize retry manager
        self.retry_manager = RetryManager(
            max_attempts=self.config.retry_attempts, base_delay=self.config.retry_delay
        )

        # Initialize batch manager
        self.batch_manager = BatchManager(
            flush_func=self._flush_batch,
            batch_size=self.config.batch_size,
            batch_timeout=self.config.batch_timeout,
        )

        logger.info("Initialized synchronous Ziz client")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ZizResponse:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            headers: Additional headers

        Returns:
            ZizResponse object
        """
        url = urljoin(self.config.api_url, endpoint)

        def _request():
            response = self.session.request(
                method=method, url=url, json=data, headers=headers, timeout=30
            )

            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                if response.status_code in self.retry_manager.retryable_status_codes:
                    raise requests.HTTPError(error_msg, response=response)
                else:
                    return ZizResponse(
                        success=False, error=error_msg, status_code=response.status_code
                    )

            return ZizResponse(
                success=True,
                data=response.json() if response.content else None,
                status_code=response.status_code,
            )

        try:
            return self.retry_manager.retry_sync(_request)
        except Exception as e:
            logger.error(f"Request failed after retries: {e}")
            return ZizResponse(
                success=False,
                error=str(e),
                status_code=getattr(e, "response", {}).get("status_code", 500),
            )

    def _flush_batch(self, batch: BatchRequest) -> None:
        """Flush a batch of events to the API."""
        api_data = batch.to_api_format()

        # Send outputs if any
        if "outputs" in api_data:
            response = self._make_request(
                "POST",
                "/v1/outputs/batch",
                data={"outputs": api_data["outputs"]},
                headers={"Idempotency-Key": f"outputs-{batch.batch_id}"},
            )
            if not response.success:
                self._handle_error(
                    Exception(f"Failed to send outputs: {response.error}"),
                    "batch output flush",
                )

        # Send interactions if any
        if "interactions" in api_data:
            response = self._make_request(
                "POST",
                "/v1/interactions/batch",
                data={"interactions": api_data["interactions"]},
                headers={"Idempotency-Key": f"interactions-{batch.batch_id}"},
            )
            if not response.success:
                self._handle_error(
                    Exception(f"Failed to send interactions: {response.error}"),
                    "batch interaction flush",
                )

    def log_output(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an output to the Ziz API.

        Args:
            content: The output content to log
            feature_id: Feature ID (uses default if not provided)
            output_id: Specific output ID (auto-generated if not provided)
            metadata: Additional metadata for the output
            **kwargs: Additional fields for the output

        Returns:
            Output ID if successful, None if failed
        """
        try:
            output = self._prepare_output(
                content=content,
                feature_id=feature_id,
                output_id=output_id,
                metadata=metadata,
                **kwargs,
            )

            # Add to batch for async processing
            self.batch_manager.add_output(output)

            # Store the output ID for convenience
            self._last_output_id = output.output_id

            logger.debug(f"Queued output {output.output_id} for batch processing")
            return output.output_id

        except Exception as e:
            self._handle_error(e, "log_output")
            return None

    def log_interaction(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an interaction to the Ziz API.

        Args:
            type: Type of interaction (e.g., "feedback", "edit")
            value: Interaction value
            output_id: Output ID to link to (uses last output if not provided)
            interaction_id: Specific interaction ID (auto-generated if not provided)
            metadata: Additional metadata for the interaction
            **kwargs: Additional fields for the interaction

        Returns:
            Interaction ID if successful, None if failed
        """
        try:
            interaction = self._prepare_interaction(
                type=type,
                value=value,
                output_id=output_id,
                interaction_id=interaction_id,
                metadata=metadata,
                **kwargs,
            )

            # Add to batch for async processing
            self.batch_manager.add_interaction(interaction)

            logger.debug(
                f"Queued interaction {interaction.interaction_id} for batch processing"
            )
            return interaction.interaction_id

        except Exception as e:
            self._handle_error(e, "log_interaction")
            return None

    def log_output_sync(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an output synchronously (bypassing batch).

        Args:
            content: The output content to log
            feature_id: Feature ID (uses default if not provided)
            output_id: Specific output ID (auto-generated if not provided)
            metadata: Additional metadata for the output
            **kwargs: Additional fields for the output

        Returns:
            Output ID if successful, None if failed
        """
        try:
            output = self._prepare_output(
                content=content,
                feature_id=feature_id,
                output_id=output_id,
                metadata=metadata,
                **kwargs,
            )

            # Send immediately
            response = self._make_request(
                "POST",
                "/v1/outputs",
                data=output.model_dump(),
                headers={"Idempotency-Key": output.output_id},
            )

            if response.success:
                self._last_output_id = output.output_id
                logger.info(f"Successfully logged output {output.output_id}")
                return output.output_id
            else:
                self._handle_error(
                    Exception(f"Failed to log output: {response.error}"),
                    "log_output_sync",
                )
                return None

        except Exception as e:
            self._handle_error(e, "log_output_sync")
            return None

    def log_interaction_sync(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an interaction synchronously (bypassing batch).

        Args:
            type: Type of interaction (e.g., "feedback", "edit")
            value: Interaction value
            output_id: Output ID to link to (uses last output if not provided)
            interaction_id: Specific interaction ID (auto-generated if not provided)
            metadata: Additional metadata for the interaction
            **kwargs: Additional fields for the interaction

        Returns:
            Interaction ID if successful, None if failed
        """
        try:
            interaction = self._prepare_interaction(
                type=type,
                value=value,
                output_id=output_id,
                interaction_id=interaction_id,
                metadata=metadata,
                **kwargs,
            )

            # Send immediately
            response = self._make_request(
                "POST",
                "/v1/interactions",
                data=interaction.model_dump(),
                headers={"Idempotency-Key": interaction.interaction_id},
            )

            if response.success:
                logger.info(
                    f"Successfully logged interaction {interaction.interaction_id}"
                )
                return interaction.interaction_id
            else:
                self._handle_error(
                    Exception(f"Failed to log interaction: {response.error}"),
                    "log_interaction_sync",
                )
                return None

        except Exception as e:
            self._handle_error(e, "log_interaction_sync")
            return None

    def flush(self) -> None:
        """Flush all pending batched events."""
        logger.info("Flushing pending events")
        self.batch_manager.flush()

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up Ziz client")
        if hasattr(self, "batch_manager"):
            self.batch_manager.shutdown()
        if hasattr(self, "session"):
            self.session.close()

    def get_pending_count(self) -> int:
        """Get the number of pending events in the batch."""
        return self.batch_manager.get_pending_count()

    def is_batch_empty(self) -> bool:
        """Check if the batch is empty."""
        return self.batch_manager.is_empty()

    # Convenience methods

    def feedback(
        self,
        value: str,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Log feedback interaction."""
        return self.log_interaction(
            type="feedback", value=value, output_id=output_id, metadata=metadata
        )

    def thumbs_up(
        self, output_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Log thumbs up feedback."""
        return self.feedback("thumbs_up", output_id, metadata)

    def thumbs_down(
        self, output_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Log thumbs down feedback."""
        return self.feedback("thumbs_down", output_id, metadata)
