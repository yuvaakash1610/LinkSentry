"""QA Automated Test Suite - API Endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    """Test GET /api/health."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "linksentry-backend"
    assert "version" in data


def test_api_model_info_endpoint():
    """Test GET /api/model-info."""
    res = client.get("/api/model-info")
    assert res.status_code == 200
    data = res.json()
    assert "text_model" in data
    assert "url_model" in data
    assert "status" in data["text_model"]
    assert "status" in data["url_model"]


def test_api_analyze_text_endpoint():
    """Test POST /api/analyze/text."""
    res = client.post("/api/analyze/text", json={"text": "URGENT: Please share your OTP 123456 now."})
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "rules_triggered" in data
    assert "request_id" in data


def test_api_analyze_url_endpoint():
    """Test POST /api/analyze/url."""
    res = client.post("/api/analyze/url", json={"url": "http://192.168.1.1/login"})
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "extracted_features" in data
    assert "url" in data


def test_api_analyze_combined_endpoint():
    """Test POST /api/analyze/combined."""
    res = client.post(
        "/api/analyze/combined",
        json={
            "text": "Your SBI account is blocked. Update KYC at link.",
            "urls": ["http://sbi-update-kyc.top/login"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "final_risk_score" in data
    assert "final_risk_level" in data
    assert "text_analysis" in data
    assert "url_analysis" in data
    assert "rules_triggered" in data
    assert "recommended_action" in data


def test_api_analyze_qr_endpoint():
    """Test POST /api/analyze/qr."""
    res = client.post("/api/analyze/qr", json={"content": "upi://pay?pa=scam@upi&pn=FakeMerchant&am=5000"})
    assert res.status_code == 200
    data = res.json()
    assert "final_risk_score" in data
    assert "final_risk_level" in data
    assert "recommended_action" in data


def test_api_feedback_endpoint():
    """Test POST /api/feedback."""
    payload = {
        "feedback": "incorrect",
        "category": "FALSE_POSITIVE",
        "request_id": "test-request-123",
        "user_notes": "False positive on legitimate notification",
    }
    res = client.post("/api/feedback", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["message"] == "Thank you for helping keep LinkSentry accurate and secure."
