from fastapi.testclient import TestClient


def test_openapi_json_endpoint(client: TestClient):
    """Verify GET /openapi.json returns HTTP 200, valid JSON, and all required routes."""
    response = client.get("/openapi.json")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers.get("content-type") == "application/json"

    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "LinkSentry Backend"

    paths = data.get("paths", {})
    required_paths = [
        "/api/health",
        "/api/model-info",
        "/api/analyze/text",
        "/api/analyze/url",
        "/api/analyze/combined",
        "/api/analyze/qr",
        "/api/feedback",
    ]

    for req_path in required_paths:
        assert req_path in paths, f"Missing required path '{req_path}' in OpenAPI schema"


def test_api_openapi_json_alias_endpoint(client: TestClient):
    """Verify GET /api/openapi.json alias endpoint returns HTTP 200 and valid JSON."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"

    data = response.json()
    assert "openapi" in data
    assert "/api/analyze/text" in data.get("paths", {})


def test_swagger_ui_docs_endpoint(client: TestClient):
    """Verify GET /docs returns HTTP 200 HTML page with proper CSP for Swagger UI resources."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "swagger-ui" in response.text.lower()

    csp = response.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in csp
    assert "default-src 'self'" in csp


def test_redoc_endpoint(client: TestClient):
    """Verify GET /redoc returns HTTP 200 HTML page with proper CSP for ReDoc resources."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "redoc" in response.text.lower()

    csp = response.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in csp
    assert "default-src 'self'" in csp
