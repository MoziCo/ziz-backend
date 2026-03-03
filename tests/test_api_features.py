"""Tests for the Feature API endpoints (Use Case 1 – Feature Creation)."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


async def test_create_feature(client: AsyncClient) -> None:
    """POST /v1/features creates a feature and returns expected fields."""
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "feat-1", "name": "Summariser", "metadata": {"team": "nlp"}},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["feature_id"] == "feat-1"
    assert body["name"] == "Summariser"
    assert body["metadata"] == {"team": "nlp"}
    assert "created_at" in body


async def test_create_feature_default_metadata(client: AsyncClient) -> None:
    """Features created without explicit metadata get an empty dict."""
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "feat-2", "name": "Chat"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["metadata"] == {}


async def test_create_feature_duplicate_returns_409(client: AsyncClient) -> None:
    """Creating a feature with the same ID twice returns 409 Conflict."""
    payload = {"feature_id": "dup", "name": "A"}
    await client.post("/v1/features", json=payload, headers=AUTH_HEADERS)
    resp = await client.post("/v1/features", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


async def test_get_feature(client: AsyncClient) -> None:
    """GET /v1/features/{id} returns the created feature."""
    await client.post(
        "/v1/features",
        json={"feature_id": "f-get", "name": "GetMe"},
        headers=AUTH_HEADERS,
    )
    resp = await client.get("/v1/features/f-get", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["feature_id"] == "f-get"
    assert resp.json()["name"] == "GetMe"


async def test_get_feature_not_found(client: AsyncClient) -> None:
    """GET /v1/features/{id} returns 404 for missing feature."""
    resp = await client.get("/v1/features/no-such", headers=AUTH_HEADERS)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


async def test_create_feature_validation_error(client: AsyncClient) -> None:
    """POST /v1/features with missing required fields returns 422."""
    resp = await client.post(
        "/v1/features",
        json={"name": "no-id"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422
