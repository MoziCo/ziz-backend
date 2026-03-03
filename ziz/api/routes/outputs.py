"""Output API routes."""

from fastapi import APIRouter, Depends, HTTPException

from ziz.api.middleware.auth import get_api_key
from ziz.api.models.batch import (
    BatchItemResult,
    BatchOutputRequest,
    BatchOutputResponse,
)
from ziz.api.models.output import OutputCreate, OutputResponse
from ziz.api.services.storage import ConflictError, NotFoundError, StorageService

router = APIRouter(prefix="/v1/outputs", tags=["outputs"])


def _get_storage() -> StorageService:
    """Placeholder dependency — overridden by app startup."""
    raise RuntimeError("Storage not initialised")  # pragma: no cover


@router.post("", response_model=OutputResponse, status_code=201)
async def create_output(
    body: OutputCreate,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> OutputResponse:
    """Upload an AI output linked to a feature."""
    try:
        return await storage.create_output(body)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{output_id}", response_model=OutputResponse)
async def get_output(
    output_id: str,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> OutputResponse:
    """Retrieve an output by ID."""
    output = await storage.get_output(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail=f"Output '{output_id}' not found")
    return output


@router.post("/batch", response_model=BatchOutputResponse, status_code=200)
async def batch_create_outputs(
    body: BatchOutputRequest,
    _key: str = Depends(get_api_key),
    storage: StorageService = Depends(_get_storage),
) -> BatchOutputResponse:
    """Create multiple outputs in one request. Supports partial failure."""
    created: list[OutputResponse] = []
    errors: list[BatchItemResult] = []

    for idx, item in enumerate(body.items):
        try:
            result = await storage.create_output(item)
            created.append(result)
        except (NotFoundError, ConflictError) as exc:
            errors.append(BatchItemResult(index=idx, success=False, error=str(exc)))

    return BatchOutputResponse(
        created=created,
        errors=errors,
        total=len(body.items),
        succeeded=len(created),
        failed=len(errors),
    )
