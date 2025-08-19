"""
Output-related API routes.

Handles CRUD operations for outputs and batch operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials

from ziz.api.middleware import api_key_auth
from ziz.api.models import (
    BatchResponse,
    ErrorResponse,
    OutputBatchCreate,
    OutputCreate,
    OutputListResponse,
    OutputResponse,
    OutputUpdate,
)
from ziz.api.services import OutputService
from ziz.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/outputs", tags=["outputs"])
output_service = OutputService()


@router.post(
    "",
    response_model=OutputResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new output",
    description="Create a new output for a feature. Output ID is optional and will be auto-generated if not provided.",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid input or feature not found",
        },
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        409: {"model": ErrorResponse, "description": "Output ID already exists"},
    },
)
async def create_output(
    output: OutputCreate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> OutputResponse:
    """Create a new output."""
    try:
        return await output_service.create_output(output)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating output: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{output_id}",
    response_model=OutputResponse,
    summary="Get an output by ID",
    description="Retrieve a specific output by its ID.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Output not found"},
    },
)
async def get_output(
    output_id: str, credentials: HTTPAuthorizationCredentials = Depends(api_key_auth)
) -> OutputResponse:
    """Get an output by ID."""
    try:
        output = await output_service.get_output(output_id)
        if not output:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Output '{output_id}' not found",
            )
        return output
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting output {output_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/{output_id}",
    response_model=OutputResponse,
    summary="Update an output",
    description="Update an existing output by its ID.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Output not found"},
    },
)
async def update_output(
    output_id: str,
    output_update: OutputUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> OutputResponse:
    """Update an output."""
    try:
        updated_output = await output_service.update_output(output_id, output_update)
        if not updated_output:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Output '{output_id}' not found",
            )
        return updated_output
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating output {output_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/batch",
    response_model=BatchResponse,
    status_code=status.HTTP_207_MULTI_STATUS,
    summary="Create multiple outputs",
    description="Create multiple outputs in a single batch operation.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
    },
)
async def create_outputs_batch(
    batch: OutputBatchCreate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> BatchResponse:
    """Create multiple outputs in batch."""
    if not settings.enable_batch_endpoints:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch endpoints are disabled"
        )

    try:
        return await output_service.create_outputs_batch(batch)
    except Exception as e:
        logger.error(f"Error in batch output creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Feature-specific output listing route
feature_outputs_router = APIRouter(prefix="/v1/features", tags=["outputs"])


@feature_outputs_router.get(
    "/{feature_id}/outputs",
    response_model=OutputListResponse,
    summary="List outputs for a feature",
    description="List all outputs for a specific feature with pagination support.",
    responses={
        400: {"model": ErrorResponse, "description": "Feature not found"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
    },
)
async def list_outputs_by_feature(
    feature_id: str,
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of outputs to return",
    ),
    offset: int = Query(default=0, ge=0, description="Number of outputs to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> OutputListResponse:
    """List outputs for a specific feature."""
    try:
        outputs, total = await output_service.list_outputs_by_feature(
            feature_id, limit, offset
        )
        return OutputListResponse(
            outputs=outputs, total=total, limit=limit, offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing outputs for feature {feature_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
