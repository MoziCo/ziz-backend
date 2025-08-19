"""
Custom exceptions and error handlers for the API.

Provides centralized error handling and custom exception types.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ZizAPIException(Exception):
    """Base exception for Ziz API."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FeatureNotFoundError(ZizAPIException):
    """Raised when a feature is not found."""

    pass


class OutputNotFoundError(ZizAPIException):
    """Raised when an output is not found."""

    pass


class InteractionNotFoundError(ZizAPIException):
    """Raised when an interaction is not found."""

    pass


class DuplicateResourceError(ZizAPIException):
    """Raised when trying to create a resource that already exists."""

    pass


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "details": getattr(exc, "details", None),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error for {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Input validation failed",
            "details": errors,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception for {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "details": None,
        },
    )


async def ziz_api_exception_handler(
    request: Request, exc: ZizAPIException
) -> JSONResponse:
    """Handle custom Ziz API exceptions."""
    logger.warning(f"ZizAPI exception for {request.url.path}: {exc.message}")

    # Map exception types to HTTP status codes
    status_code_map = {
        FeatureNotFoundError: status.HTTP_404_NOT_FOUND,
        OutputNotFoundError: status.HTTP_404_NOT_FOUND,
        InteractionNotFoundError: status.HTTP_404_NOT_FOUND,
        DuplicateResourceError: status.HTTP_409_CONFLICT,
    }

    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__.lower().replace("error", "_error"),
            "message": exc.message,
            "details": exc.details,
        },
    )
