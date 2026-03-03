"""Tests for the Output API endpoints (Use Case 2 – Upload Output)."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


# -- helpers ------------------------------------------------------------------

async def _create_feature(client: AsyncClient, feature_id: str = "feat-1") -> None:
    await client.post(
        "/v1/features",
        json={"feature_id": feature_id, "name": "Test Feature"},
        headers=AUTH_HEADERS,
    )


# -- tests --------------------------------------------------------------------


async def test_create_output(client: AsyncClient) -> None:
    """POST /v1/outputs returns output_id, feature_id, content, metadata."""
    await _create_feature(client)
    resp = await client.post(
        "/v1/outputs",
        json={
            "output_id": "out-1",
            "feature_id": "feat-1",
            "content": "Hello world",
            "metadata": {"model": "gpt-4"},
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["output_id"] == "out-1"
    assert body["feature_id"] == "feat-1"
    assert body["content"] == "Hello world"
    assert body["metadata"] == {"model": "gpt-4"}
    assert "created_at" in body


async def test_create_output_missing_feature_returns_404(client: AsyncClient) -> None:
    """Creating an output for a non-existent feature returns 404."""
    resp = await client.post(
        "/v1/outputs",
        json={
            "output_id": "out-x",
            "feature_id": "no-feature",
            "content": "text",
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


async def test_create_output_duplicate_returns_409(client: AsyncClient) -> None:
    """Creating an output with the same output_id twice returns 409."""
    await _create_feature(client)
    payload = {"output_id": "dup-out", "feature_id": "feat-1", "content": "x"}
    await client.post("/v1/outputs", json=payload, headers=AUTH_HEADERS)
    resp = await client.post("/v1/outputs", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 409


async def test_get_output(client: AsyncClient) -> None:
    """GET /v1/outputs/{id} returns the created output."""
    await _create_feature(client)
    await client.post(
        "/v1/outputs",
        json={"output_id": "out-g", "feature_id": "feat-1", "content": "data"},
        headers=AUTH_HEADERS,
    )
    resp = await client.get("/v1/outputs/out-g", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["output_id"] == "out-g"


async def test_get_output_not_found(client: AsyncClient) -> None:
    """GET /v1/outputs/{id} returns 404 for missing output."""
    resp = await client.get("/v1/outputs/missing", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_create_output_validation_error(client: AsyncClient) -> None:
    """POST /v1/outputs with missing content returns 422."""
    await _create_feature(client)
    resp = await client.post(
        "/v1/outputs",
        json={"output_id": "o-bad", "feature_id": "feat-1"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422
