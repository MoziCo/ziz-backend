"""Interaction API routes."""

from fastapi import APIRouter, Depends, HTTPException

from ziz.api.middleware.auth import get_api_key
from ziz.api.models.batch import (
    BatchInteractionRequest,
    BatchInteractionResponse,
    BatchItemResult,
)
from ziz.api.models.interaction import InteractionCreate, InteractionResponse
from ziz.api.services.storage import ConflictError, NotFoundError, StorageService

router = APIRouter(prefix="/v1/interactions", tags=["interactions"])


def _get_storage() -> StorageService:
    """Placeholder dependency — overridden by app startup."""
    raise RuntimeError("Storage not initialised")  # pragma: no cover


@router.post("", response_model=InteractionResponse, status_code=201)
async def create_interaction(
    body: InteractionCreate,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> InteractionResponse:
    """Attach a user interaction to an output."""
    try:
        return await storage.create_interaction(body)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: str,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> InteractionResponse:
    """Retrieve an interaction by ID."""
    interaction = await storage.get_interaction(interaction_id)
    if interaction is None:
        raise HTTPException(
            status_code=404, detail=f"Interaction '{interaction_id}' not found"
        )
    return interaction


@router.post("/batch", response_model=BatchInteractionResponse, status_code=200)
async def batch_create_interactions(
    body: BatchInteractionRequest,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> BatchInteractionResponse:
    """Create multiple interactions in one request. Supports partial failure."""
    created: list[InteractionResponse] = []
    errors: list[BatchItemResult] = []

    for idx, item in enumerate(body.items):
        try:
            result = await storage.create_interaction(item)
            created.append(result)
        except (NotFoundError, ConflictError) as exc:
            errors.append(BatchItemResult(index=idx, success=False, error=str(exc)))

    return BatchInteractionResponse(
        created=created,
        errors=errors,
        total=len(body.items),
        succeeded=len(created),
        failed=len(errors),
    )
