"""
Interaction-related API routes.

Handles CRUD operations for interactions and batch operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials

from ziz.api.middleware import api_key_auth
from ziz.api.models import (
    BatchResponse,
    ErrorResponse,
    InteractionBatchCreate,
    InteractionCreate,
    InteractionListResponse,
    InteractionResponse,
    InteractionUpdate,
)
from ziz.api.services import InteractionService
from ziz.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/interactions", tags=["interactions"])
interaction_service = InteractionService()


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new interaction",
    description="Create a new interaction for an output. Interaction ID is optional and will be auto-generated if not provided.",
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid input or output not found",
        },
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        409: {"model": ErrorResponse, "description": "Interaction ID already exists"},
    },
)
async def create_interaction(
    interaction: InteractionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> InteractionResponse:
    """Create a new interaction."""
    try:
        return await interaction_service.create_interaction(interaction)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{interaction_id}",
    response_model=InteractionResponse,
    summary="Get an interaction by ID",
    description="Retrieve a specific interaction by its ID.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Interaction not found"},
    },
)
async def get_interaction(
    interaction_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> InteractionResponse:
    """Get an interaction by ID."""
    try:
        interaction = await interaction_service.get_interaction(interaction_id)
        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interaction '{interaction_id}' not found",
            )
        return interaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interaction {interaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/{interaction_id}",
    response_model=InteractionResponse,
    summary="Update an interaction",
    description="Update an existing interaction by its ID.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Interaction not found"},
    },
)
async def update_interaction(
    interaction_id: str,
    interaction_update: InteractionUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> InteractionResponse:
    """Update an interaction."""
    try:
        updated_interaction = await interaction_service.update_interaction(
            interaction_id, interaction_update
        )
        if not updated_interaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interaction '{interaction_id}' not found",
            )
        return updated_interaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interaction {interaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/batch",
    response_model=BatchResponse,
    status_code=status.HTTP_207_MULTI_STATUS,
    summary="Create multiple interactions",
    description="Create multiple interactions in a single batch operation.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
    },
)
async def create_interactions_batch(
    batch: InteractionBatchCreate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> BatchResponse:
    """Create multiple interactions in batch."""
    if not settings.enable_batch_endpoints:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch endpoints are disabled"
        )

    try:
        return await interaction_service.create_interactions_batch(batch)
    except Exception as e:
        logger.error(f"Error in batch interaction creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Output-specific interaction listing route
output_interactions_router = APIRouter(prefix="/v1/outputs", tags=["interactions"])


@output_interactions_router.get(
    "/{output_id}/interactions",
    response_model=InteractionListResponse,
    summary="List interactions for an output",
    description="List all interactions for a specific output with pagination support.",
    responses={
        400: {"model": ErrorResponse, "description": "Output not found"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
    },
)
async def list_interactions_by_output(
    output_id: str,
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of interactions to return",
    ),
    offset: int = Query(default=0, ge=0, description="Number of interactions to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> InteractionListResponse:
    """List interactions for a specific output."""
    try:
        interactions, total = await interaction_service.list_interactions_by_output(
            output_id, limit, offset
        )
        return InteractionListResponse(
            interactions=interactions, total=total, limit=limit, offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing interactions for output {output_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
