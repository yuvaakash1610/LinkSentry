from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from app.schemas.analyze import (
    CombinedAnalysisResponse,
    RiskLevel,
    TextAnalysisRequest,
    TextAnalysisResponse,
    UrlAnalysisRequest,
    UrlAnalysisResponse,
)


# --- TEXT ANALYSIS TESTS ---

def test_analyze_text_valid_suspicious(client: TestClient):
    payload = {
        "text": "URGENT: Your SBI bank account is suspended due to KYC expired. Verify immediately at http://192.168.1.1/sbi-kyc",
        "source": "manual_paste",
        "language_hint": "en",
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("suspicious", "high_risk")
    assert data["category"] in ("urgency_coercion", "credential_harvesting", "scam")
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["reasons"], list) and len(data["reasons"]) > 0
    assert isinstance(data["indicators"], list) and len(data["indicators"]) > 0
    assert data["model_status"] == "unavailable"  # No fabricated ML
    assert len(data["extracted_urls"]) == 1
    assert "http://192.168.1.1/sbi-kyc" in data["extracted_urls"]
    assert len(data["rules_triggered"]) > 0
    assert data["recommended_action"] in (
        "Do not provide sensitive information or make a payment until independently verified.",
        "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
    )


def test_analyze_text_valid_benign(client: TestClient):
    payload = {
        "text": "Hi Dad, I will reach home around 7 PM for dinner. See you soon!",
        "source": "sms",
        "language_hint": "en",
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "low"
    assert data["risk_score"] < 0.30
    assert data["category"] == "benign"
    assert data["recommended_action"] == "Continue normally, while remaining cautious."


def test_analyze_text_empty_and_whitespace(client: TestClient):
    # Empty string
    r1 = client.post("/api/analyze/text", json={"text": ""})
    assert r1.status_code == 422
    assert r1.json()["error"]["code"] == "INVALID_INPUT"

    # Whitespace only
    r2 = client.post("/api/analyze/text", json={"text": "   \n\t  "})
    assert r2.status_code == 422
    assert r2.json()["error"]["code"] == "INVALID_INPUT"

    # Missing text field
    r3 = client.post("/api/analyze/text", json={})
    assert r3.status_code == 422
    assert r3.json()["error"]["code"] == "INVALID_INPUT"


def test_analyze_text_malformed(client: TestClient):
    # Text is non-string (int/dict)
    r = client.post("/api/analyze/text", json={"text": 12345})
    r2 = client.post("/api/analyze/text", json={"text": {"nested": "object"}})
    assert r2.status_code == 422
    assert r2.json()["error"]["code"] == "INVALID_INPUT"


# --- URL ANALYSIS TESTS ---

def test_analyze_url_valid_suspicious(client: TestClient):
    payload = {
        "url": "http://192.168.4.10:8080/secure/login",
        "source": "manual_paste",
    }
    response = client.post("/api/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ("suspicious", "high_risk")
    assert data["hostname"] == "192.168.4.10"
    assert "ip_address_host" in data["indicators"]
    assert "URL_IP_HOST" in data["triggered_rules"]
    assert data["model_status"] == "unavailable"
    assert isinstance(data["extracted_features"], dict)
    assert data["extracted_features"]["is_ip_address"] is True


def test_analyze_url_valid_benign(client: TestClient):
    payload = {
        "url": "https://www.google.com/search?q=cybersecurity",
        "source": "browser_intercept",
    }
    response = client.post("/api/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "low"
    assert data["risk_score"] < 0.30
    assert data["hostname"] == "www.google.com"
    assert data["registered_domain"] == "google.com"


def test_analyze_url_sensitive_params_masked(client: TestClient):
    payload = {
        "url": "https://bank.example.com/login?token=supersecret123&otp=849201",
    }
    response = client.post("/api/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "supersecret123" not in data["url"]
    assert "849201" not in data["url"]


def test_analyze_url_invalid(client: TestClient):
    # Empty string
    r1 = client.post("/api/analyze/url", json={"url": ""})
    assert r1.status_code == 422

    # Whitespace only
    r2 = client.post("/api/analyze/url", json={"url": "   "})
    assert r2.status_code == 422

    # Unsupported scheme (e.g. javascript:, file:)
    r3 = client.post("/api/analyze/url", json={"url": "javascript:alert(1)"})
    assert r3.status_code == 422
    assert "unsupported url scheme" in r3.json()["error"]["message"].lower()

    # Missing netloc / invalid syntax
    r4 = client.post("/api/analyze/url", json={"url": "http://"})
    assert r4.status_code == 422


# --- COMBINED ANALYSIS TESTS ---

def test_analyze_combined_with_both_text_and_urls(client: TestClient):
    payload = {
        "text": "Your account will be blocked today. Update KYC immediately: http://bank-verify.example",
        "urls": ["http://bank-verify.example"],
        "source": "manual_paste",
        "language_hint": "en",
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert 0.0 <= data["final_risk_score"] <= 1.0
    assert data["final_risk_level"] in ("verify_independently", "suspicious", "high_risk")
    assert data["text_analysis"] is not None
    assert len(data["url_analysis"]) >= 1
    assert isinstance(data["rules_triggered"], list)
    assert data["recommended_action"] in (
        "Verify the request using an official source before taking action.",
        "Do not provide sensitive information or make a payment until independently verified.",
        "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
    )


def test_analyze_combined_text_only(client: TestClient):
    payload = {
        "text": "Normal safe conversation with friend.",
        "urls": [],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["final_risk_level"] == "low"
    assert data["text_analysis"] is not None
    assert len(data["url_analysis"]) == 0
    assert data["recommended_action"] == "Continue normally, while remaining cautious."


def test_analyze_combined_urls_only(client: TestClient):
    payload = {
        "text": None,
        "urls": ["https://www.example.com"],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["text_analysis"] is None
    assert len(data["url_analysis"]) == 1


def test_analyze_combined_missing_both_inputs(client: TestClient):
    # Both text and urls empty
    payload = {
        "text": "",
        "urls": [],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_INPUT"


# --- QR ANALYSIS TESTS ---

def test_analyze_qr_valid(client: TestClient):
    payload = {
        "content": "https://claim-cashback-reward.xyz/lottery",
        "source": "qr",
    }
    response = client.post("/api/analyze/qr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert 0.0 <= data["final_risk_score"] <= 1.0
    assert len(data["url_analysis"]) >= 1


def test_analyze_qr_empty(client: TestClient):
    r1 = client.post("/api/analyze/qr", json={"content": ""})
    assert r1.status_code == 422
    assert r1.json()["error"]["code"] == "INVALID_INPUT"

    r2 = client.post("/api/analyze/qr", json={"content": "   "})
    assert r2.status_code == 422


# --- SCHEMA BOUNDS & INVALID RISK VALUE TESTS ---

def test_schema_risk_bounds():
    with pytest.raises(ValidationError):
        TextAnalysisResponse(
            risk_score=1.5,
            risk_level=RiskLevel.HIGH_RISK,
            category="scam",
            confidence=0.8,
            reasons=[],
            indicators=[],
        )

    with pytest.raises(ValidationError):
        CombinedAnalysisResponse(
            request_id="test",
            final_risk_score=-0.1,
            final_risk_level=RiskLevel.LOW,
            recommended_action="Continue normally, while remaining cautious.",
        )
