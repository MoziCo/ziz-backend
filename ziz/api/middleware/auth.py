"""
Authentication middleware for API key validation.

Provides API key-based authentication for securing endpoints.
"""

import logging
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ziz.core.config import settings

logger = logging.getLogger(__name__)


class APIKeyAuth(HTTPBearer):
    """API Key authentication using Bearer token."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        """Validate API key from Authorization header or X-API-Key header."""
        # First try Authorization header (Bearer token)
        try:
            credentials = await super().__call__(request)
            if credentials and self._is_valid_api_key(credentials.credentials):
                return credentials
        except HTTPException:
            pass

        # Then try X-API-Key header
        api_key = request.headers.get(settings.api_key_header)
        if api_key and self._is_valid_api_key(api_key):
            return HTTPAuthorizationCredentials(scheme="ApiKey", credentials=api_key)

        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

    def _is_valid_api_key(self, api_key: str) -> bool:
        """Validate the API key."""
        # In production, this should validate against a database or external service
        # For MVP, we'll use a simple comparison with the secret key
        return api_key == settings.secret_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication on protected routes."""

    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request and validate API key if required."""
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate API key
        api_key_auth = APIKeyAuth(auto_error=False)
        try:
            credentials = await api_key_auth(request)
            if credentials:
                # Add API key info to request state for logging
                request.state.api_key = credentials.credentials[:8] + "..."
                logger.info(
                    f"Authenticated request from API key: {request.state.api_key}"
                )
            else:
                # No valid credentials found
                logger.warning(
                    f"Authentication failed for {request.url.path}: Invalid or missing API key"
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "unauthorized",
                        "message": "Invalid or missing API key",
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException as e:
            # Convert HTTPException to JSONResponse to avoid 500 errors
            logger.warning(f"Authentication failed for {request.url.path}: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "unauthorized", "message": e.detail},
                headers=getattr(e, "headers", {}),
            )
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "authentication_error",
                    "message": "Authentication error",
                },
            )

        response = await call_next(request)
        return response


# Global API key authentication instance
api_key_auth = APIKeyAuth()
