"""
Basic API tests for Ziz API.

Tests the main API endpoints and functionality.
"""

from fastapi.testclient import TestClient

from ziz.api.main import app

# Create test client without raising exceptions for HTTP errors
client = TestClient(app, raise_server_exceptions=False)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")

    # This might fail if MongoDB is not running, which is expected in CI
    # We'll check for either success or service unavailable
    assert response.status_code in [200, 503]

    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert data["service"] == "ziz-api"
        assert data["version"] == "0.1.0"
    else:
        assert "error" in data


def test_docs_endpoint():
    """Test the OpenAPI docs endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test the OpenAPI schema endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert data["info"]["title"] == "Ziz Evaluation API"
    assert data["info"]["version"] == "0.1.0"


def test_api_key_required():
    """Test that API key is required for protected endpoints."""
    # Test feature creation without API key
    response = client.post("/v1/features", json={"name": "Test Feature"})
    assert response.status_code == 401

    # Test output creation without API key
    response = client.post(
        "/v1/outputs", json={"feature_id": "test-feature", "content": "test content"}
    )
    assert response.status_code == 401

    # Test interaction creation without API key
    response = client.post(
        "/v1/interactions",
        json={"output_id": "test-output", "type": "feedback", "value": "thumbs_up"},
    )
    assert response.status_code == 401


def test_api_key_auth_header():
    """Test API key authentication via Authorization header."""
    headers = {"Authorization": "Bearer your-secret-key-change-in-production"}

    # This will likely fail due to database connection, but should pass auth
    response = client.post(
        "/v1/features", json={"name": "Test Feature"}, headers=headers
    )
    # Should not be 401 (unauthorized)
    assert response.status_code != 401


def test_api_key_auth_custom_header():
    """Test API key authentication via X-API-Key header."""
    headers = {"X-API-Key": "your-secret-key-change-in-production"}

    # This will likely fail due to database connection, but should pass auth
    response = client.post(
        "/v1/features", json={"name": "Test Feature"}, headers=headers
    )
    # Should not be 401 (unauthorized)
    assert response.status_code != 401


def test_invalid_api_key():
    """Test authentication with invalid API key."""
    headers = {"Authorization": "Bearer invalid-key"}

    response = client.post(
        "/v1/features", json={"name": "Test Feature"}, headers=headers
    )
    assert response.status_code == 401
