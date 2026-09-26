from fastapi.testclient import TestClient


def test_api_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "linksentry-backend"
    assert data["version"] == "1.0.0"

    # Strict check: Do not leak secrets or internal environment/file paths
    forbidden_keys = [
        "env",
        "environment",
        "secret",
        "key",
        "path",
        "model_path",
        "text_model_path",
        "url_model_path",
        "settings",
    ]
    for key in forbidden_keys:
        assert key not in data, f"Leaked sensitive key in health response: {key}"


def test_root_health_fallback(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "linksentry-backend"
