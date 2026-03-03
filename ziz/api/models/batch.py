"""Batch operation model schemas."""

from pydantic import BaseModel, Field

from ziz.api.models.interaction import InteractionCreate, InteractionResponse
from ziz.api.models.output import OutputCreate, OutputResponse


class BatchItemResult(BaseModel):
    """Result of a single item in a batch operation."""

    index: int = Field(..., description="Index of the item in the batch request")
    success: bool
    error: str | None = None


class BatchOutputRequest(BaseModel):
    """Request schema for batch output creation."""

    items: list[OutputCreate] = Field(..., min_length=1, description="List of outputs to create")


class BatchOutputResponse(BaseModel):
    """Response schema for batch output creation."""

    created: list[OutputResponse] = Field(default_factory=list)
    errors: list[BatchItemResult] = Field(default_factory=list)
    total: int
    succeeded: int
    failed: int


class BatchInteractionRequest(BaseModel):
    """Request schema for batch interaction creation."""

    items: list[InteractionCreate] = Field(
        ..., min_length=1, description="List of interactions to create"
    )


class BatchInteractionResponse(BaseModel):
    """Response schema for batch interaction creation."""

    created: list[InteractionResponse] = Field(default_factory=list)
    errors: list[BatchItemResult] = Field(default_factory=list)
    total: int
    succeeded: int
    failed: int
