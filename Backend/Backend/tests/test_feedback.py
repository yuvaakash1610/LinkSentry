from fastapi.testclient import TestClient


def test_submit_feedback_correct(client: TestClient):
    payload = {
        "feedback": "correct",
        "request_id": "test-req-1234",
        "input_text": "Normal message",
        "user_notes": "Model accurately flagged safe",
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "feedback_id" in data


def test_submit_feedback_incorrect(client: TestClient):
    payload = {
        "feedback": "incorrect",
        "request_id": "test-req-5678",
        "input_url": "https://legit-site.com",
        "user_notes": "False alarm on internal company portal",
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_submit_feedback_uncertain(client: TestClient):
    payload = {
        "feedback": "uncertain",
        "user_notes": "Not sure if sender was legitimate",
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_submit_invalid_feedback_rating(client: TestClient):
    payload = {
        "feedback": "invalid_rating",
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_submit_empty_feedback_payload(client: TestClient):
    response = client.post("/api/feedback", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"
