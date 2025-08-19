"""
Health check and system status routes.

Provides endpoints for monitoring system health and status.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from ziz.api.models import ErrorResponse, HealthResponse
from ziz.api.services.mongodb_storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies.",
    responses={
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def health_check() -> HealthResponse:
    """Perform a comprehensive health check."""
    try:
        # Check database connectivity
        db_health = await storage_service.health_check()
        database_status = (
            "connected" if db_health.get("status") == "healthy" else "disconnected"
        )

        # If database is unhealthy, return service unavailable
        if database_status == "disconnected":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed",
            )

        return HealthResponse(
            status="healthy",
            service="ziz-api",
            version="0.1.0",
            timestamp=datetime.now(UTC),
            database=database_status,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed",
        )


@router.get(
    "/",
    summary="Root endpoint",
    description="Basic API information and status.",
)
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Ziz API is running",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
