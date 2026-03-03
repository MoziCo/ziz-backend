"""Tests for the Query API endpoints (Use Case 4 – Query)."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


# -- helpers ------------------------------------------------------------------

async def _seed(client: AsyncClient) -> None:
    """Create feature + output + interaction for querying."""
    await client.post(
        "/v1/features",
        json={"feature_id": "feat-q", "name": "Q"},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/v1/outputs",
        json={"output_id": "out-q1", "feature_id": "feat-q", "content": "a"},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/v1/outputs",
        json={"output_id": "out-q2", "feature_id": "feat-q", "content": "b"},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/v1/interactions",
        json={"interaction_id": "int-q1", "output_id": "out-q1", "interaction_type": "like"},
        headers=AUTH_HEADERS,
    )
    await client.post(
        "/v1/interactions",
        json={"interaction_id": "int-q2", "output_id": "out-q1", "interaction_type": "edit"},
        headers=AUTH_HEADERS,
    )


# -- tests: list outputs by feature ------------------------------------------


async def test_list_outputs_by_feature(client: AsyncClient) -> None:
    """GET /v1/features/{id}/outputs returns all outputs for the feature."""
    await _seed(client)
    resp = await client.get("/v1/features/feat-q/outputs", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    ids = {o["output_id"] for o in data}
    assert ids == {"out-q1", "out-q2"}


async def test_list_outputs_empty(client: AsyncClient) -> None:
    """A feature with no outputs returns an empty list."""
    await client.post(
        "/v1/features",
        json={"feature_id": "empty-f", "name": "E"},
        headers=AUTH_HEADERS,
    )
    resp = await client.get("/v1/features/empty-f/outputs", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_outputs_feature_not_found(client: AsyncClient) -> None:
    """Querying outputs for a non-existent feature returns 404."""
    resp = await client.get("/v1/features/nope/outputs", headers=AUTH_HEADERS)
    assert resp.status_code == 404


# -- tests: list interactions by output ---------------------------------------


async def test_list_interactions_by_output(client: AsyncClient) -> None:
    """GET /v1/outputs/{id}/interactions returns all interactions."""
    await _seed(client)
    resp = await client.get("/v1/outputs/out-q1/interactions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    types = {i["interaction_type"] for i in data}
    assert types == {"like", "edit"}


async def test_list_interactions_empty(client: AsyncClient) -> None:
    """An output with no interactions returns an empty list."""
    await _seed(client)
    resp = await client.get("/v1/outputs/out-q2/interactions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_interactions_output_not_found(client: AsyncClient) -> None:
    """Querying interactions for a non-existent output returns 404."""
    resp = await client.get("/v1/outputs/nope/interactions", headers=AUTH_HEADERS)
    assert resp.status_code == 404
