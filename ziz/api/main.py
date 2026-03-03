"""
Ziz API Main Application

FastAPI application entry point for the Ziz evaluation system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ziz.api.routes.features import _get_storage as _feat_dep
from ziz.api.routes.features import router as features_router
from ziz.api.routes.interactions import _get_storage as _int_dep
from ziz.api.routes.interactions import router as interactions_router
from ziz.api.routes.outputs import _get_storage as _out_dep
from ziz.api.routes.outputs import router as outputs_router
from ziz.api.routes.query import _get_storage as _query_dep
from ziz.api.routes.query import router as query_router
from ziz.api.services.storage import InMemoryStorage, StorageService

app = FastAPI(
    title="Ziz Evaluation API",
    description="User-experience-driven evaluation framework for AI applications",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Storage dependency -------------------------------------------------------
# Default to in-memory; production would swap this for a MongoDB-backed impl.
_storage: StorageService = InMemoryStorage()


def _provide_storage() -> StorageService:
    """FastAPI dependency that returns the shared storage instance."""
    return _storage


# Override the placeholder dependency in every router
app.dependency_overrides[_feat_dep] = _provide_storage
app.dependency_overrides[_out_dep] = _provide_storage
app.dependency_overrides[_int_dep] = _provide_storage
app.dependency_overrides[_query_dep] = _provide_storage

# -- Register routers ---------------------------------------------------------
app.include_router(features_router)
app.include_router(outputs_router)
app.include_router(interactions_router)
app.include_router(query_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"message": "Ziz API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Detailed health check endpoint."""
    return {"status": "healthy", "service": "ziz-api"}


def main() -> None:
    """Entry point for running the API server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
