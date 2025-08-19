"""
Feature-related API routes.

Handles CRUD operations for features.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials

from ziz.api.middleware import api_key_auth
from ziz.api.models import (
    ErrorResponse,
    FeatureCreate,
    FeatureListResponse,
    FeatureResponse,
    FeatureUpdate,
)
from ziz.api.services import FeatureService
from ziz.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/features", tags=["features"])
feature_service = FeatureService()


@router.post(
    "",
    response_model=FeatureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature",
    description="Create a new feature. Feature ID is optional and will be auto-generated if not provided.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        409: {"model": ErrorResponse, "description": "Feature ID already exists"},
    },
)
async def create_feature(
    feature: FeatureCreate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> FeatureResponse:
    """Create a new feature."""
    try:
        return await feature_service.create_feature(feature)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/{feature_id}",
    response_model=FeatureResponse,
    summary="Get a feature by ID",
    description="Retrieve a specific feature by its ID.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Feature not found"},
    },
)
async def get_feature(
    feature_id: str, credentials: HTTPAuthorizationCredentials = Depends(api_key_auth)
) -> FeatureResponse:
    """Get a feature by ID."""
    try:
        feature = await feature_service.get_feature(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature '{feature_id}' not found",
            )
        return feature
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature {feature_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put(
    "/{feature_id}",
    response_model=FeatureResponse,
    summary="Update a feature",
    description="Update an existing feature by its ID.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        404: {"model": ErrorResponse, "description": "Feature not found"},
    },
)
async def update_feature(
    feature_id: str,
    feature_update: FeatureUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> FeatureResponse:
    """Update a feature."""
    try:
        updated_feature = await feature_service.update_feature(
            feature_id, feature_update
        )
        if not updated_feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature '{feature_id}' not found",
            )
        return updated_feature
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature {feature_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "",
    response_model=FeatureListResponse,
    summary="List features",
    description="List all features with pagination support.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
    },
)
async def list_features(
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of features to return",
    ),
    offset: int = Query(default=0, ge=0, description="Number of features to skip"),
    credentials: HTTPAuthorizationCredentials = Depends(api_key_auth),
) -> FeatureListResponse:
    """List features with pagination."""
    try:
        features, total = await feature_service.list_features(limit, offset)
        return FeatureListResponse(
            features=features, total=total, limit=limit, offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
