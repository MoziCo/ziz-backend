"""Interaction model schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InteractionCreate(BaseModel):
    """Request schema for creating an interaction."""

    interaction_id: str = Field(
        ..., min_length=1, description="Client-provided unique interaction ID"
    )
    output_id: str = Field(..., min_length=1, description="Output this interaction belongs to")
    interaction_type: str = Field(
        ...,
        min_length=1,
        description="Type of interaction (e.g. like, dislike, edit, retry, copy)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")
    timestamp: datetime | None = Field(
        default=None, description="Client-provided timestamp; server uses current time if omitted"
    )


class InteractionResponse(BaseModel):
    """Response schema for an interaction."""

    interaction_id: str
    output_id: str
    interaction_type: str
    metadata: dict[str, Any]
    timestamp: datetime
    created_at: datetime
