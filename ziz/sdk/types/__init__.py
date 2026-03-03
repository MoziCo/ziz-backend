"""SDK Type definitions module."""

from typing import Any

from pydantic import BaseModel, Field


class BatchRequest(BaseModel):
    """Generic batch request wrapper used by the SDK client."""

    endpoint: str = Field(..., description="Target API endpoint path")
    items: list[dict[str, Any]] = Field(..., description="List of items to send in the batch")


__all__ = ["BatchRequest"]
