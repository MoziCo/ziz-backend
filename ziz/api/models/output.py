"""Output model schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OutputCreate(BaseModel):
    """Request schema for creating an output."""

    output_id: str = Field(..., min_length=1, description="Client-provided unique output ID")
    feature_id: str = Field(..., min_length=1, description="Feature this output belongs to")
    content: str = Field(..., min_length=1, description="The AI output content (text)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class OutputResponse(BaseModel):
    """Response schema for an output."""

    output_id: str
    feature_id: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime
