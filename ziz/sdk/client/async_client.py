"""
Asynchronous Ziz SDK client implementation.

Provides an async interface for logging outputs and interactions.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp

from ..types import BatchRequest, ZizResponse
from ..utils import RetryManager, get_logger
from .base import BaseClient
from .batch import BatchManager

logger = get_logger("async_client")


class AsyncZizClient(BaseClient):
    """Asynchronous client for the Ziz API."""

    def __init__(self, **kwargs):
        """Initialize the asynchronous client."""
        super().__init__(**kwargs)

        self._session: Optional[aiohttp.ClientSession] = None

        # Initialize retry manager
        self.retry_manager = RetryManager(
            max_attempts=self.config.retry_attempts, base_delay=self.config.retry_delay
        )

        # Initialize batch manager
        self.batch_manager = BatchManager(
            flush_func=self._flush_batch_sync,  # We'll wrap this for async
            batch_size=self.config.batch_size,
            batch_timeout=self.config.batch_timeout,
        )

        logger.info("Initialized asynchronous Ziz client")

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "ziz-python-sdk/1.0.0",
                },
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ZizResponse:
        """
        Make an async HTTP request to the API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            headers: Additional headers

        Returns:
            ZizResponse object
        """
        url = urljoin(self.config.api_url, endpoint)

        async def _request():
            async with self.session.request(
                method=method, url=url, json=data, headers=headers
            ) as response:
                response_text = await response.text()

                # Check for HTTP errors
                if response.status >= 400:
                    error_msg = f"HTTP {response.status}: {response_text}"
                    if response.status in self.retry_manager.retryable_status_codes:
                        exc = aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_msg,
                        )
                        exc.status_code = response.status
                        raise exc
                    else:
                        return ZizResponse(
                            success=False, error=error_msg, status_code=response.status
                        )

                response_data = None
                if response_text:
                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        pass

                return ZizResponse(
                    success=True, data=response_data, status_code=response.status
                )

        try:
            return await self.retry_manager.retry_async(_request)
        except Exception as e:
            logger.error(f"Request failed after retries: {e}")
            return ZizResponse(
                success=False, error=str(e), status_code=getattr(e, "status_code", 500)
            )

    def _flush_batch_sync(self, batch: BatchRequest) -> None:
        """Synchronous wrapper for async batch flushing."""
        # Create a new event loop for this thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            if loop.is_running():
                # If we're in an async context, schedule the flush
                asyncio.create_task(self._flush_batch_async(batch))
            else:
                # Run the flush in the current thread
                loop.run_until_complete(self._flush_batch_async(batch))
        except Exception as e:
            logger.error(f"Failed to flush batch: {e}")

    async def _flush_batch_async(self, batch: BatchRequest) -> None:
        """Flush a batch of events to the API asynchronously."""
        api_data = batch.to_api_format()

        # Send outputs if any
        if "outputs" in api_data:
            response = await self._make_request(
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
            response = await self._make_request(
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

    async def log_output(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an output to the Ziz API asynchronously.

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

    async def log_interaction(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an interaction to the Ziz API asynchronously.

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

    async def log_output_immediate(
        self,
        content: Any,
        feature_id: Optional[str] = None,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an output immediately (bypassing batch).

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
            response = await self._make_request(
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
                    "log_output_immediate",
                )
                return None

        except Exception as e:
            self._handle_error(e, "log_output_immediate")
            return None

    async def log_interaction_immediate(
        self,
        type: str,
        value: Any,
        output_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Log an interaction immediately (bypassing batch).

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
            response = await self._make_request(
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
                    "log_interaction_immediate",
                )
                return None

        except Exception as e:
            self._handle_error(e, "log_interaction_immediate")
            return None

    def flush(self) -> None:
        """Flush all pending batched events."""
        logger.info("Flushing pending events")
        self.batch_manager.flush()

    async def aflush(self) -> None:
        """Async version of flush."""
        logger.info("Flushing pending events asynchronously")
        # Force flush any remaining events
        if not self.batch_manager.is_empty():
            # We need to manually flush here since the batch manager
            # flush is synchronous
            with self.batch_manager._lock:
                if self.batch_manager._events:
                    events_to_flush = list(self.batch_manager._events)
                    self.batch_manager._events.clear()

                    batch = BatchRequest(events=events_to_flush)
                    await self._flush_batch_async(batch)

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up async Ziz client")
        if hasattr(self, "batch_manager"):
            self.batch_manager.shutdown()

        # Close aiohttp session if it exists
        if self._session and not self._session.closed:
            # Schedule session close in the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._session.close())
                else:
                    loop.run_until_complete(self._session.close())
            except RuntimeError:
                # If no event loop, we can't close properly
                pass

    async def aclose(self) -> None:
        """Async cleanup method."""
        logger.info("Async cleanup of Ziz client")
        await self.aflush()
        if self._session and not self._session.closed:
            await self._session.close()

    def get_pending_count(self) -> int:
        """Get the number of pending events in the batch."""
        return self.batch_manager.get_pending_count()

    def is_batch_empty(self) -> bool:
        """Check if the batch is empty."""
        return self.batch_manager.is_empty()

    # Convenience methods

    async def feedback(
        self,
        value: str,
        output_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Log feedback interaction."""
        return await self.log_interaction(
            type="feedback", value=value, output_id=output_id, metadata=metadata
        )

    async def thumbs_up(
        self, output_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Log thumbs up feedback."""
        return await self.feedback("thumbs_up", output_id, metadata)

    async def thumbs_down(
        self, output_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Log thumbs down feedback."""
        return await self.feedback("thumbs_down", output_id, metadata)

    # Context manager support

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
