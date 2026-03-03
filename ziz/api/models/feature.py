"""Feature model schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FeatureCreate(BaseModel):
    """Request schema for creating a feature."""

    feature_id: str = Field(..., min_length=1, description="Client-provided unique feature ID")
    name: str = Field(..., min_length=1, description="Human-readable feature name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class FeatureResponse(BaseModel):
    """Response schema for a feature."""

    feature_id: str
    name: str
    metadata: dict[str, Any]
    created_at: datetime
