"""End-to-end flow test: create feature -> create output -> attach interaction -> query."""

import pytest
from httpx import AsyncClient

from tests.conftest import AUTH_HEADERS

pytestmark = pytest.mark.asyncio


async def test_full_flow(client: AsyncClient) -> None:
    """Exercise the complete basic flow from feature creation to querying."""

    # 1. Create a feature
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "chat", "name": "Chat Assistant", "metadata": {"version": "1.0"}},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    feature = resp.json()
    assert feature["feature_id"] == "chat"

    # 2. Upload outputs for that feature
    resp = await client.post(
        "/v1/outputs",
        json={
            "output_id": "resp-1",
            "feature_id": "chat",
            "content": "Here is the answer to your question.",
            "metadata": {"model": "gpt-4", "latency_ms": 320},
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    output = resp.json()
    assert output["output_id"] == "resp-1"
    assert output["feature_id"] == "chat"

    resp = await client.post(
        "/v1/outputs",
        json={
            "output_id": "resp-2",
            "feature_id": "chat",
            "content": "Another response.",
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201

    # 3. Attach interactions to the first output
    resp = await client.post(
        "/v1/interactions",
        json={
            "interaction_id": "act-1",
            "output_id": "resp-1",
            "interaction_type": "like",
            "metadata": {"ui": "thumb-up"},
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201
    interaction = resp.json()
    assert interaction["output_id"] == "resp-1"
    assert interaction["interaction_type"] == "like"

    resp = await client.post(
        "/v1/interactions",
        json={
            "interaction_id": "act-2",
            "output_id": "resp-1",
            "interaction_type": "copy",
        },
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 201

    # 4. Query: list outputs for the feature
    resp = await client.get("/v1/features/chat/outputs", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    outputs = resp.json()
    assert len(outputs) == 2
    assert {o["output_id"] for o in outputs} == {"resp-1", "resp-2"}

    # 5. Query: list interactions for the first output
    resp = await client.get("/v1/outputs/resp-1/interactions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    interactions = resp.json()
    assert len(interactions) == 2
    assert {i["interaction_type"] for i in interactions} == {"like", "copy"}

    # 6. Query: second output has no interactions
    resp = await client.get("/v1/outputs/resp-2/interactions", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []

    # 7. Verify idempotency: duplicate feature creation returns 409
    resp = await client.post(
        "/v1/features",
        json={"feature_id": "chat", "name": "Chat Assistant"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 409
