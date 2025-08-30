"""
Core data models for the Ziz SDK.

These models represent the data structures used throughout the SDK.
"""

import os
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class ZizConfig(BaseModel):
    """Configuration for the Ziz SDK client."""

    api_key: str = Field(..., description="API key for authentication")
    api_url: str = Field(
        default="https://api.ziz.ai", description="Base URL for the Ziz API"
    )
    feature_id: Optional[str] = Field(
        default=None, description="Default feature ID for all operations"
    )
    batch_size: int = Field(
        default=100, description="Maximum number of events to batch before flushing"
    )
    batch_timeout: float = Field(
        default=5.0, description="Maximum time in seconds to wait before flushing batch"
    )
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )
    retry_delay: float = Field(
        default=1.0, description="Initial delay between retries in seconds"
    )
    allow_content: bool = Field(
        default=False, description="Whether to allow content logging (privacy setting)"
    )
    strict_mode: bool = Field(
        default=False, description="Whether to raise exceptions on errors"
    )

    @classmethod
    def from_env(cls, **overrides) -> "ZizConfig":
        """Create configuration from environment variables."""
        config = {
            "api_key": os.getenv("ZIZ_API_KEY", ""),
            "api_url": os.getenv("ZIZ_API_URL", "https://api.ziz.ai"),
            "feature_id": os.getenv("ZIZ_FEATURE_ID"),
            "batch_size": int(os.getenv("ZIZ_BATCH_SIZE", "100")),
            "batch_timeout": float(os.getenv("ZIZ_BATCH_TIMEOUT", "5.0")),
            "retry_attempts": int(os.getenv("ZIZ_RETRY_ATTEMPTS", "3")),
            "retry_delay": float(os.getenv("ZIZ_RETRY_DELAY", "1.0")),
            "allow_content": os.getenv("ZIZ_ALLOW_CONTENT", "false").lower() == "true",
            "strict_mode": os.getenv("ZIZ_STRICT_MODE", "false").lower() == "true",
        }
        config.update(overrides)
        return cls(**config)


class EventType(str, Enum):
    """Types of events that can be logged."""

    OUTPUT = "output"
    INTERACTION = "interaction"


class Feature(BaseModel):
    """Represents a feature in the Ziz system."""

    feature_id: str = Field(..., description="Unique identifier for the feature")
    name: str = Field(..., description="Human-readable name for the feature")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the feature"
    )


class Output(BaseModel):
    """Represents an output to be logged."""

    output_id: Optional[str] = Field(
        default=None, description="Unique identifier for the output"
    )
    feature_id: str = Field(..., description="Feature this output belongs to")
    content: Any = Field(..., description="The output content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the output"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="When the output was generated"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing."""
        if self.output_id is None:
            self.output_id = str(uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class Interaction(BaseModel):
    """Represents an interaction with an output."""

    interaction_id: Optional[str] = Field(
        default=None, description="Unique identifier for the interaction"
    )
    output_id: str = Field(..., description="Output this interaction is linked to")
    type: str = Field(..., description="Type of interaction (e.g., feedback, edit)")
    value: Any = Field(..., description="Value of the interaction")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the interaction"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="When the interaction occurred"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing."""
        if self.interaction_id is None:
            self.interaction_id = str(uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class ZizEvent(BaseModel):
    """Represents an event to be sent to the Ziz API."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType = Field(..., description="Type of event")
    data: Union[Output, Interaction] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    client_event_id: str = Field(default_factory=lambda: str(uuid4()))

    @property
    def idempotency_key(self) -> str:
        """Generate idempotency key for this event."""
        return f"{self.event_type.value}-{self.client_event_id}"


class ZizResponse(BaseModel):
    """Response from the Ziz API."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Response data if successful"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if unsuccessful"
    )
    status_code: int = Field(..., description="HTTP status code")


class BatchRequest(BaseModel):
    """Represents a batch of events to send."""

    events: List[ZizEvent] = Field(..., description="List of events to send")
    batch_id: str = Field(default_factory=lambda: str(uuid4()))

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to API format for batch requests."""
        outputs = []
        interactions = []

        for event in self.events:
            if event.event_type == EventType.OUTPUT:
                output_data = event.data.model_dump()
                outputs.append(output_data)
            elif event.event_type == EventType.INTERACTION:
                interaction_data = event.data.model_dump()
                interactions.append(interaction_data)

        result = {}
        if outputs:
            result["outputs"] = outputs
        if interactions:
            result["interactions"] = interactions

        return result
