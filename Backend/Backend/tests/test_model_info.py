from fastapi.testclient import TestClient


def test_get_model_info(client: TestClient):
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()

    assert "text_model" in data
    assert "url_model" in data

    text_model = data["text_model"]
    assert "name" in text_model
    assert "version" in text_model
    assert "status" in text_model
    assert text_model["status"] in ("unavailable", "active")

    url_model = data["url_model"]
    assert "name" in url_model
    assert "version" in url_model
    assert "status" in url_model
    assert url_model["status"] in ("unavailable", "active")

    # Strict check: Never expose filesystem paths or secrets
    sensitive_keys = ["path", "file", "filesystem", "secret", "dir", "directory"]
    for model_dict in (text_model, url_model):
        for key in sensitive_keys:
            assert key not in model_dict, f"Exposed sensitive key '{key}' in model-info"
            assert not any(
                "\\" in str(v) or "/" in str(v) for v in model_dict.values()
            ), "Exposed file path in model info metadata values!"
