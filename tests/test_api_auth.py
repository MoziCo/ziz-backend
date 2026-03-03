"""Tests for API key authentication."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


async def test_missing_api_key_returns_401(client: AsyncClient) -> None:
    """Requests without X-API-Key header should be rejected."""
    resp = await client.post("/v1/features", json={"feature_id": "f1", "name": "F1"})
    assert resp.status_code == 401
    assert "Invalid or missing API key" in resp.json()["detail"]


async def test_wrong_api_key_returns_401(client: AsyncClient) -> None:
    """Requests with an incorrect API key should be rejected."""
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "f1", "name": "F1"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


async def test_valid_api_key_accepted(client: AsyncClient) -> None:
    """Requests with the correct API key should succeed."""
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "f1", "name": "F1"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201


async def test_auth_required_on_all_endpoints(client: AsyncClient) -> None:
    """All data endpoints require authentication."""
    endpoints = [
        ("POST", "/v1/features"),
        ("GET", "/v1/features/any"),
        ("POST", "/v1/outputs"),
        ("GET", "/v1/outputs/any"),
        ("POST", "/v1/outputs/batch"),
        ("POST", "/v1/interactions"),
        ("GET", "/v1/interactions/any"),
        ("POST", "/v1/interactions/batch"),
        ("GET", "/v1/features/any/outputs"),
        ("GET", "/v1/outputs/any/interactions"),
    ]
    for method, path in endpoints:
        resp = await client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} should require auth"
