"""
Pydantic models for Ziz API.

These models define the request/response schemas for the API endpoints.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseZizModel(BaseModel):
    """Base model with common configuration."""

    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }


# Feature Models
class FeatureCreate(BaseZizModel):
    """Model for creating a new feature."""

    feature_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FeatureResponse(BaseZizModel):
    """Model for feature response."""

    feature_id: str
    name: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FeatureUpdate(BaseZizModel):
    """Model for updating a feature."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


# Output Models
class OutputCreate(BaseZizModel):
    """Model for creating a new output."""

    output_id: Optional[str] = None
    feature_id: str = Field(..., min_length=1)
    content: Any = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class OutputResponse(BaseZizModel):
    """Model for output response."""

    output_id: str
    feature_id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    created_at: datetime
    updated_at: datetime


class OutputUpdate(BaseZizModel):
    """Model for updating an output."""

    content: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


# Interaction Models
class InteractionCreate(BaseZizModel):
    """Model for creating a new interaction."""

    interaction_id: Optional[str] = None
    output_id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1, max_length=100)
    value: Any = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class InteractionResponse(BaseZizModel):
    """Model for interaction response."""

    interaction_id: str
    output_id: str
    type: str
    value: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    created_at: datetime
    updated_at: datetime


class InteractionUpdate(BaseZizModel):
    """Model for updating an interaction."""

    type: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


# Batch Models
class OutputBatchCreate(BaseZizModel):
    """Model for batch creating outputs."""

    outputs: List[OutputCreate] = Field(..., min_length=1, max_length=1000)


class InteractionBatchCreate(BaseZizModel):
    """Model for batch creating interactions."""

    interactions: List[InteractionCreate] = Field(..., min_length=1, max_length=1000)


class BatchResponse(BaseZizModel):
    """Model for batch operation response."""

    success_count: int
    failure_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# List/Pagination Models
class PaginationParams(BaseZizModel):
    """Model for pagination parameters."""

    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class FeatureListResponse(BaseZizModel):
    """Model for feature list response."""

    features: List[FeatureResponse]
    total: int
    limit: int
    offset: int


class OutputListResponse(BaseZizModel):
    """Model for output list response."""

    outputs: List[OutputResponse]
    total: int
    limit: int
    offset: int


class InteractionListResponse(BaseZizModel):
    """Model for interaction list response."""

    interactions: List[InteractionResponse]
    total: int
    limit: int
    offset: int


# Error Models
class ErrorResponse(BaseZizModel):
    """Model for error responses."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseZizModel):
    """Model for validation error responses."""

    error: str = "validation_error"
    message: str
    details: List[Dict[str, Any]]


# Health Models
class HealthResponse(BaseZizModel):
    """Model for health check response."""

    status: str = "healthy"
    service: str = "ziz-api"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    database: str = "connected"
