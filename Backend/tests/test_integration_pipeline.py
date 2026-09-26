from fastapi.testclient import TestClient
import pytest
from app.schemas.analyze import (
    CombinedAnalysisResponse,
    RiskLevel,
    TextAnalysisResponse,
    UrlAnalysisResponse,
)


def test_text_analysis_pipeline(client: TestClient):
    """
    Test Text Pipeline:
    request -> validation -> preprocessing -> URL extraction -> text analysis -> rules -> final result
    """
    payload = {
        "text": "Your electricity supply will be disconnected today due to unpaid bill. Pay immediately at http://192.168.1.50/pay",
        "source": "sms",
        "language_hint": "en",
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validated response model
    validated = TextAnalysisResponse(**data)
    assert 0.0 <= validated.risk_score <= 1.0
    assert validated.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)
    # URL extraction check
    assert len(validated.extracted_urls) == 1
    assert validated.extracted_urls[0] == "http://192.168.1.50/pay"
    # Rules triggered
    assert len(validated.rules_triggered) > 0
    # Recommended action non-definitive
    assert validated.recommended_action in (
        "Do not provide sensitive information or make a payment until independently verified.",
        "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
    )
    # Verify no forbidden certainty claims
    for banned in ["100% scam", "definitely malicious", "guaranteed protection"]:
        assert banned not in validated.recommended_action.lower()
        for r in validated.reasons:
            assert banned not in r.lower()


def test_url_analysis_pipeline(client: TestClient):
    """
    Test URL Pipeline:
    request -> validation -> URL parsing -> feature extraction -> ML if available -> rules -> final result
    """
    payload = {
        "url": "http://user:password@10.0.0.1:8080/secure/update-kyc.php?token=xyz123&otp=998877",
        "source": "manual_paste",
    }
    response = client.post("/api/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = UrlAnalysisResponse(**data)
    assert 0.0 <= validated.risk_score <= 1.0
    assert validated.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)
    # Host and features
    assert validated.hostname == "10.0.0.1"
    assert validated.extracted_features["is_ip_address"] is True
    assert validated.extracted_features["has_at_deception"] is True
    # Masking check: token and otp masked in reported url
    assert "xyz123" not in validated.url
    assert "998877" not in validated.url
    # Triggered rules
    assert "URL_IP_HOST" in validated.triggered_rules or "RULE_IP_HOST" in validated.triggered_rules


def test_combined_pipeline_with_multiple_and_duplicate_urls(client: TestClient):
    """
    Test Combined Pipeline:
    request -> validation -> text preprocessing -> URL extraction -> text analysis
    -> URL analysis -> rules -> risk fusion -> explanation -> recommendation
    with multiple URLs and duplicate removal.
    """
    payload = {
        "text": "Dear customer, your bank account is blocked. Visit https://www.google.com and also http://192.168.1.1/unlock",
        "urls": [
            "https://www.google.com",  # Duplicate of url in text (benign)
            "http://192.168.1.1/unlock",  # Duplicate of url in text (suspicious IP)
            "https://update-kyc.top/verify",  # Third distinct URL (suspicious TLD)
        ],
        "source": "manual_paste",
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = CombinedAnalysisResponse(**data)
    assert validated.request_id is not None
    assert 0.0 <= validated.final_risk_score <= 1.0
    assert validated.final_risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)
    assert validated.text_analysis is not None

    # Verify URL deduplication: 3 unique URLs total
    assert len(validated.url_analysis) == 3
    urls_evaluated = [u.url for u in validated.url_analysis]

    # Verify that URLs do NOT have identical risk scores (independent per-URL evaluation)
    scores = [u.risk_score for u in validated.url_analysis]
    # google.com should have lower score than raw IP or .top domain
    google_res = next(u for u in validated.url_analysis if "google.com" in u.url)
    ip_res = next(u for u in validated.url_analysis if "192.168.1.1" in u.url)
    assert google_res.risk_score < ip_res.risk_score

    # Explanation and recommendation
    assert validated.summary is not None
    assert validated.recommended_action == "Do not click the link or provide credentials, OTPs, PINs, or payment details."


def test_combined_pipeline_text_only(client: TestClient):
    """Combined analysis with no URLs: must normalize without assuming missing signals are safe."""
    payload = {
        "text": "Hello, please find attached the meeting minutes for yesterday's discussion.",
        "urls": [],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = CombinedAnalysisResponse(**data)
    assert validated.text_analysis is not None
    assert len(validated.url_analysis) == 0
    assert validated.final_risk_level == RiskLevel.LOW
    assert validated.recommended_action == "Continue normally, while remaining cautious."


def test_combined_pipeline_url_only(client: TestClient):
    """Combined analysis with URL only: must normalize without assuming missing text is safe."""
    payload = {
        "text": None,
        "urls": ["http://192.168.1.100/admin/login"],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = CombinedAnalysisResponse(**data)
    assert validated.text_analysis is None
    assert len(validated.url_analysis) == 1
    assert validated.url_analysis[0].risk_score > 0.40
    assert validated.final_risk_score > 0.40


def test_critical_escalation_on_credential_theft(client: TestClient):
    """Critical threats like OTP theft should trigger escalation and clear actionable guidance."""
    payload = {
        "text": "Please share your OTP 482910 immediately with the agent to prevent SIM deactivation.",
        "urls": [],
    }
    response = client.post("/api/analyze/combined", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = CombinedAnalysisResponse(**data)
    assert validated.final_risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)
    assert "RULE_OTP_REQUEST" in validated.rules_triggered or "TXT_CREDENTIAL_SOLICITATION" in validated.rules_triggered
    assert "Do not click the link or provide credentials, OTPs, PINs, or payment details." in validated.recommended_action or \
           "Do not provide sensitive information" in validated.recommended_action


def test_benign_otp_notification_does_not_falsely_escalate(client: TestClient):
    """Standard legitimate bank delivery 'Your OTP is 123456. Do not share' must not trigger theft rule."""
    payload = {
        "text": "Your OTP for transaction of Rs 500 is 123456. Do not share this OTP with anyone for security reasons.",
        "urls": [],
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    validated = TextAnalysisResponse(**data)
    # Should not trigger RULE_OTP_REQUEST (which is only for solicitation)
    assert "RULE_OTP_REQUEST" not in validated.rules_triggered
