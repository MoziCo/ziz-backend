"""Tests for the Interaction API endpoints (Use Case 3 – Attach Interactions)."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


# -- helpers ------------------------------------------------------------------

async def _seed(client: AsyncClient) -> None:
    """Create a feature and an output to link interactions against."""
    await client.post(
        "/v1/features",
        json={"feature_id": "feat-1", "name": "F"},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/v1/outputs",
        json={"output_id": "out-1", "feature_id": "feat-1", "content": "txt"},
        headers=AUTH_HEADERS,
    )


# -- tests --------------------------------------------------------------------


async def test_create_interaction(client: AsyncClient) -> None:
    """POST /v1/interactions returns interaction_id, output_id, type, timestamp."""
    await _seed(client)
    resp = await client.post(
        "/v1/interactions",
        json={
            "interaction_id": "int-1",
            "output_id": "out-1",
            "interaction_type": "like",
            "metadata": {"source": "ui"},
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["interaction_id"] == "int-1"
    assert body["output_id"] == "out-1"
    assert body["interaction_type"] == "like"
    assert body["metadata"] == {"source": "ui"}
    assert "timestamp" in body
    assert "created_at" in body


async def test_create_interaction_with_client_timestamp(client: AsyncClient) -> None:
    """Client-provided timestamp is preserved."""
    await _seed(client)
    ts = "2025-06-01T12:00:00Z"
    resp = await client.post(
        "/v1/interactions",
        json={
            "interaction_id": "int-ts",
            "output_id": "out-1",
            "interaction_type": "edit",
            "timestamp": ts,
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    assert "2025-06-01" in resp.json()["timestamp"]


async def test_create_interaction_missing_output_returns_404(client: AsyncClient) -> None:
    """Creating an interaction for a non-existent output returns 404."""
    resp = await client.post(
        "/v1/interactions",
        json={
            "interaction_id": "int-x",
            "output_id": "no-out",
            "interaction_type": "retry",
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 404


async def test_create_interaction_duplicate_returns_409(client: AsyncClient) -> None:
    """Creating an interaction with the same ID twice returns 409."""
    await _seed(client)
    payload = {
        "interaction_id": "dup-int",
        "output_id": "out-1",
        "interaction_type": "copy",
    }
    await client.post("/v1/interactions", json=payload, headers=AUTH_HEADERS)
    resp = await client.post("/v1/interactions", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 409


async def test_get_interaction(client: AsyncClient) -> None:
    """GET /v1/interactions/{id} returns the created interaction."""
    await _seed(client)
    await client.post(
        "/v1/interactions",
        json={"interaction_id": "int-g", "output_id": "out-1", "interaction_type": "like"},
        headers=AUTH_HEADERS,
    )
    resp = await client.get("/v1/interactions/int-g", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["interaction_id"] == "int-g"


async def test_get_interaction_not_found(client: AsyncClient) -> None:
    """GET /v1/interactions/{id} returns 404 for missing interaction."""
    resp = await client.get("/v1/interactions/nope", headers=AUTH_HEADERS)
    assert resp.status_code == 404


async def test_create_interaction_validation_error(client: AsyncClient) -> None:
    """POST /v1/interactions with missing type returns 422."""
    await _seed(client)
    resp = await client.post(
        "/v1/interactions",
        json={"interaction_id": "bad", "output_id": "out-1"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422
