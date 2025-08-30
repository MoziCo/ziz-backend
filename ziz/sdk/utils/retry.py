"""
Retry logic for the Ziz SDK.

Implements exponential backoff and jitter for robust API calls.
"""

import asyncio
import random
import time
from typing import Any, Callable, Optional

from .logging import get_logger

logger = get_logger("retry")


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""

    pass


class RetryManager:
    """Manages retry logic with exponential backoff and jitter."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: Optional[set] = None,
    ):
        """
        Initialize retry manager.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
            retryable_status_codes: HTTP status codes that should trigger retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes or {
            429,
            500,
            502,
            503,
            504,
        }

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = self.base_delay * (self.exponential_base**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter: random value between 0.5 and 1.5 times the delay
            jitter_factor = 0.5 + random.random()
            delay *= jitter_factor

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if we should retry based on the exception and attempt number.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-based)

        Returns:
            True if we should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False

        # Check for HTTP status code errors
        if hasattr(exception, "status_code"):
            return exception.status_code in self.retryable_status_codes

        # Check for network-related errors
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return True

        # Check for explicitly retryable errors
        if isinstance(exception, RetryableError):
            return True

        return False

    def retry_sync(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute a function with retry logic (synchronous).

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful function execution

        Raises:
            Last exception if all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    logger.debug(f"Not retrying after attempt {attempt + 1}: {e}")
                    break

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)

        logger.error(f"All {self.max_attempts + 1} attempts failed")
        raise last_exception

    async def retry_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute an async function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful function execution

        Raises:
            Last exception if all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    logger.debug(f"Not retrying after attempt {attempt + 1}: {e}")
                    break

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)

        logger.error(f"All {self.max_attempts + 1} attempts failed")
        raise last_exception
