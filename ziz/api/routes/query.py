"""Query API routes for listing related resources."""

from fastapi import APIRouter, Depends, HTTPException

from ziz.api.middleware.auth import get_api_key
from ziz.api.models.interaction import InteractionResponse
from ziz.api.models.output import OutputResponse
from ziz.api.services.storage import StorageService

router = APIRouter(prefix="/v1", tags=["query"])


def _get_storage() -> StorageService:
    """Placeholder dependency — overridden by app startup."""
    raise RuntimeError("Storage not initialised")  # pragma: no cover


@router.get(
    "/features/{feature_id}/outputs",
    response_model=list[OutputResponse],
)
async def list_outputs_by_feature(
    feature_id: str,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> list[OutputResponse]:
    """List all outputs for a given feature."""
    feature = await storage.get_feature(feature_id)
    if feature is None:
        raise HTTPException(status_code=404, detail=f"Feature '{feature_id}' not found")
    return await storage.list_outputs_by_feature(feature_id)


@router.get(
    "/outputs/{output_id}/interactions",
    response_model=list[InteractionResponse],
)
async def list_interactions_by_output(
    output_id: str,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> list[InteractionResponse]:
    """List all interactions for a given output."""
    output = await storage.get_output(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail=f"Output '{output_id}' not found")
    return await storage.list_interactions_by_output(output_id)
