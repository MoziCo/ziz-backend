"""Tests for the Batch API endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


# -- helpers ------------------------------------------------------------------

async def _create_feature(client: AsyncClient, fid: str = "feat-b") -> None:
    await client.post(
        "/v1/features",
        json={"feature_id": fid, "name": "Batch"},
        headers=AUTH_HEADERS,
    )


async def _create_output(client: AsyncClient, oid: str = "out-b") -> None:
    await client.post(
        "/v1/outputs",
        json={"output_id": oid, "feature_id": "feat-b", "content": "x"},
        headers=AUTH_HEADERS,
    )


# -- batch output tests -------------------------------------------------------


async def test_batch_outputs_all_succeed(client: AsyncClient) -> None:
    """POST /v1/outputs/batch succeeds for all valid items."""
    await _create_feature(client)
    resp = await client.post(
        "/v1/outputs/batch",
        json={
            "items": [
                {"output_id": "bo-1", "feature_id": "feat-b", "content": "a"},
                {"output_id": "bo-2", "feature_id": "feat-b", "content": "b"},
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["succeeded"] == 2
    assert body["failed"] == 0
    assert len(body["created"]) == 2


async def test_batch_outputs_partial_failure(client: AsyncClient) -> None:
    """Batch returns partial results when some items fail."""
    await _create_feature(client)
    # First create one output to cause a conflict
    await _create_output(client, "dup-bo")
    resp = await client.post(
        "/v1/outputs/batch",
        json={
            "items": [
                {"output_id": "dup-bo", "feature_id": "feat-b", "content": "dup"},
                {"output_id": "new-bo", "feature_id": "feat-b", "content": "ok"},
                {"output_id": "bad-bo", "feature_id": "no-feat", "content": "bad"},
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["succeeded"] == 1
    assert body["failed"] == 2
    assert len(body["errors"]) == 2
    # Check error indices
    error_indices = {e["index"] for e in body["errors"]}
    assert error_indices == {0, 2}


# -- batch interaction tests ---------------------------------------------------


async def test_batch_interactions_all_succeed(client: AsyncClient) -> None:
    """POST /v1/interactions/batch succeeds for all valid items."""
    await _create_feature(client)
    await _create_output(client, "out-bi")
    resp = await client.post(
        "/v1/interactions/batch",
        json={
            "items": [
                {"interaction_id": "bi-1", "output_id": "out-bi", "interaction_type": "like"},
                {"interaction_id": "bi-2", "output_id": "out-bi", "interaction_type": "copy"},
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["succeeded"] == 2
    assert body["failed"] == 0


async def test_batch_interactions_partial_failure(client: AsyncClient) -> None:
    """Batch returns partial results with error details."""
    await _create_feature(client)
    await _create_output(client, "out-bi2")
    # Pre-create to cause duplicate
    await client.post(
        "/v1/interactions",
        json={"interaction_id": "dup-bi", "output_id": "out-bi2", "interaction_type": "like"},
        headers=AUTH_HEADERS,
    )
    resp = await client.post(
        "/v1/interactions/batch",
        json={
            "items": [
                {"interaction_id": "dup-bi", "output_id": "out-bi2", "interaction_type": "like"},
                {"interaction_id": "ok-bi", "output_id": "out-bi2", "interaction_type": "edit"},
                {"interaction_id": "bad-bi", "output_id": "no-out", "interaction_type": "retry"},
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["succeeded"] == 1
    assert body["failed"] == 2
