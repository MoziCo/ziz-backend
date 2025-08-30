"""
Batch management for the Ziz SDK.

Handles batching of events with automatic flushing based on size and time.
"""

import atexit
import threading
import time
from collections import deque
from typing import Any, Callable, Optional

from ..types import BatchRequest, EventType, Interaction, Output, ZizEvent
from ..utils import get_logger

logger = get_logger("batch")


class BatchManager:
    """Manages batching of events with automatic flushing."""

    def __init__(
        self,
        flush_func: Callable[[BatchRequest], Any],
        batch_size: int = 100,
        batch_timeout: float = 5.0,
        auto_flush: bool = True,
    ):
        """
        Initialize batch manager.

        Args:
            flush_func: Function to call when flushing batches
            batch_size: Maximum events per batch
            batch_timeout: Maximum time to wait before flushing (seconds)
            auto_flush: Whether to automatically flush batches
        """
        self.flush_func = flush_func
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.auto_flush = auto_flush

        self._events: deque = deque()
        self._lock = threading.Lock()
        self._last_flush_time = time.time()
        self._flush_timer: Optional[threading.Timer] = None
        self._shutdown = False

        if auto_flush:
            self._start_auto_flush()

        # Register cleanup
        atexit.register(self.shutdown)

    def add_output(self, output: Output) -> None:
        """Add an output to the batch."""
        event = ZizEvent(event_type=EventType.OUTPUT, data=output)
        self._add_event(event)

    def add_interaction(self, interaction: Interaction) -> None:
        """Add an interaction to the batch."""
        event = ZizEvent(event_type=EventType.INTERACTION, data=interaction)
        self._add_event(event)

    def _add_event(self, event: ZizEvent) -> None:
        """Add an event to the batch."""
        with self._lock:
            if self._shutdown:
                logger.warning("Batch manager is shutdown, ignoring event")
                return

            self._events.append(event)
            logger.debug(f"Added event to batch. Queue size: {len(self._events)}")

            # Check if we need to flush due to size
            if len(self._events) >= self.batch_size:
                self._flush_now()

    def _start_auto_flush(self) -> None:
        """Start the auto-flush timer."""
        if self._shutdown:
            return

        self._flush_timer = threading.Timer(self.batch_timeout, self._auto_flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _auto_flush(self) -> None:
        """Auto-flush based on timeout."""
        with self._lock:
            if self._shutdown:
                return

            current_time = time.time()
            if (
                current_time - self._last_flush_time >= self.batch_timeout
                and len(self._events) > 0
            ):
                self._flush_now()

            # Schedule next auto-flush
            if self.auto_flush:
                self._start_auto_flush()

    def _flush_now(self) -> None:
        """Flush events immediately (assumes lock is held)."""
        if not self._events:
            return

        # Create batch from current events
        events_to_flush = list(self._events)
        self._events.clear()
        self._last_flush_time = time.time()

        batch = BatchRequest(events=events_to_flush)

        logger.info(f"Flushing batch with {len(events_to_flush)} events")

        # Release lock before calling flush function to avoid deadlocks
        threading.Thread(target=self._flush_batch, args=(batch,), daemon=True).start()

    def _flush_batch(self, batch: BatchRequest) -> None:
        """Flush a batch in a background thread."""
        try:
            self.flush_func(batch)
            logger.debug(f"Successfully flushed batch {batch.batch_id}")
        except Exception as e:
            logger.error(f"Failed to flush batch {batch.batch_id}: {e}")
            # In a production system, you might want to retry or store failed batches

    def flush(self) -> None:
        """Manually flush all pending events."""
        with self._lock:
            if self._events:
                self._flush_now()

    def shutdown(self) -> None:
        """Shutdown the batch manager and flush all pending events."""
        logger.info("Shutting down batch manager")

        with self._lock:
            self._shutdown = True

            # Cancel auto-flush timer
            if self._flush_timer:
                self._flush_timer.cancel()
                self._flush_timer = None

            # Flush any remaining events
            if self._events:
                self._flush_now()

        # Wait a moment for background flush to complete
        time.sleep(0.1)

    def get_pending_count(self) -> int:
        """Get the number of pending events."""
        with self._lock:
            return len(self._events)

    def is_empty(self) -> bool:
        """Check if the batch is empty."""
        with self._lock:
            return len(self._events) == 0
