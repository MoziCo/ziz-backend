"""
Database models for MongoDB.

These models represent the data structure stored in MongoDB collections.
"""

from datetime import UTC, datetime
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseDocument(BaseModel):
    """Base document model with common fields."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }


class FeatureDocument(BaseDocument):
    """Feature document for MongoDB storage."""

    feature_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutputDocument(BaseDocument):
    """Output document for MongoDB storage."""

    output_id: str = Field(default_factory=lambda: str(uuid4()))
    feature_id: str
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InteractionDocument(BaseDocument):
    """Interaction document for MongoDB storage."""

    interaction_id: str = Field(default_factory=lambda: str(uuid4()))
    output_id: str
    type: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
