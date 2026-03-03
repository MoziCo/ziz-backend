"""Shared test fixtures for the Ziz API test suite."""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from ziz.api.main import app, _provide_storage
from ziz.api.routes.features import _get_storage as _feat_dep
from ziz.api.routes.interactions import _get_storage as _int_dep
from ziz.api.routes.outputs import _get_storage as _out_dep
from ziz.api.routes.query import _get_storage as _query_dep
from ziz.api.services.storage import InMemoryStorage

API_KEY = "test-api-key"
AUTH_HEADERS = {"X-API-Key": API_KEY}


@pytest_asyncio.fixture()
async def storage() -> InMemoryStorage:
    """Fresh in-memory storage for each test."""
    return InMemoryStorage()


@pytest_asyncio.fixture()
async def client(storage: InMemoryStorage) -> AsyncIterator[AsyncClient]:
    """Async HTTP test client backed by a fresh storage instance."""

    def _override() -> InMemoryStorage:
        return storage

    app.dependency_overrides[_feat_dep] = _override
    app.dependency_overrides[_out_dep] = _override
    app.dependency_overrides[_int_dep] = _override
    app.dependency_overrides[_query_dep] = _override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore default overrides
    app.dependency_overrides[_feat_dep] = _provide_storage
    app.dependency_overrides[_out_dep] = _provide_storage
    app.dependency_overrides[_int_dep] = _provide_storage
    app.dependency_overrides[_query_dep] = _provide_storage
