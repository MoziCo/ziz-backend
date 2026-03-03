"""API key authentication middleware."""

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Default key for development/testing; override via ZIZ_API_KEY env var.
DEFAULT_API_KEY = "test-api-key"


def _get_expected_key() -> str:
    """Return the expected API key from environment or default."""
    return os.environ.get("ZIZ_API_KEY", DEFAULT_API_KEY)


async def get_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """Validate the API key from the request header.

    Returns the validated key on success, raises 401 on failure.
    """
    if api_key is None or api_key != _get_expected_key():
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
