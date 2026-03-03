"""Feature API routes."""

from fastapi import APIRouter, Depends, HTTPException

from ziz.api.middleware.auth import get_api_key
from ziz.api.models.feature import FeatureCreate, FeatureResponse
from ziz.api.services.storage import ConflictError, StorageService

router = APIRouter(prefix="/v1/features", tags=["features"])


def _get_storage() -> StorageService:
    """Placeholder dependency — overridden by app startup."""
    raise RuntimeError("Storage not initialised")  # pragma: no cover


@router.post("", response_model=FeatureResponse, status_code=201)
async def create_feature(
    body: FeatureCreate,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> FeatureResponse:
    """Create a new feature with a client-provided ID (idempotent)."""
    try:
        return await storage.create_feature(body)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(
    feature_id: str,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> FeatureResponse:
    """Retrieve a feature by ID."""
    feature = await storage.get_feature(feature_id)
    if feature is None:
        raise HTTPException(status_code=404, detail=f"Feature '{feature_id}' not found")
    return feature
