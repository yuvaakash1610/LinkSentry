import uuid
from fastapi.testclient import TestClient


def test_request_id_generated_automatically(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) > 10


def test_request_id_preserved_when_supplied(client: TestClient):
    custom_id = f"test-trace-{uuid.uuid4()}"
    response = client.get("/api/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_validation_error_format_on_invalid_request(client: TestClient):
    # Missing required 'text' field in text analysis
    response = client.post("/api/analyze/text", json={})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_INPUT"
    assert "message" in data["error"]
    assert "request_id" in data["error"]
    assert data["error"]["request_id"] == response.headers.get("X-Request-ID")


def test_not_found_error_format(client: TestClient):
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert "request_id" in data["error"]


def test_security_headers_present(client: TestClient):
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
