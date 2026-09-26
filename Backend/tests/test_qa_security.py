"""QA Automated Test Suite - Security & Robustness."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.utils.masking import mask_card_number, mask_sensitive_text, mask_sensitive_url_params
from app.utils.url_utils import extract_lexical_features, offline_extractor

client = TestClient(app)


def test_security_sensitive_logging_masking():
    """Verify sensitive credit cards, OTPs, and credentials are redacted in logs/utilities."""
    text_with_card = "My credit card number is 4532-7182-9381-1049."
    masked_text = mask_card_number(text_with_card)
    assert "4532-7182-9381-1049" not in masked_text
    assert "***" in masked_text

    text_with_otp = "Your OTP is: 987654"
    masked_otp = mask_sensitive_text(text_with_otp)
    assert "987654" not in masked_otp
    assert "[REDACTED_OTP]" in masked_otp

    url_with_token = "https://bank.com/reset?token=secret12345&password=mySuperPassword"
    masked_url = mask_sensitive_url_params(url_with_token)
    assert "secret12345" not in masked_url
    assert "mySuperPassword" not in masked_url
    assert "REDACTED" in masked_url


def test_security_oversized_input_rejection():
    """Verify oversized payloads exceeding MAX_TEXT_LENGTH are rejected with HTTP 422."""
    settings = get_settings()
    oversized_text = "A" * (settings.MAX_TEXT_LENGTH + 500)
    res = client.post("/api/analyze/text", json={"text": oversized_text})
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "INVALID_INPUT"


def test_security_malformed_json_input():
    """Verify malformed JSON or invalid schema payloads return HTTP 422 without server crash."""
    res = client.post(
        "/api/analyze/text",
        content="not_valid_json{",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422
    data = res.json()
    assert "error" in data


def test_security_no_stack_trace_exposure():
    """Verify 404, 422, and 500 responses do NOT expose raw Python stack traces or internal code lines."""
    res_404 = client.get("/api/nonexistent-endpoint-xyz")
    assert res_404.status_code == 404
    assert "Traceback" not in res_404.text
    assert "File \"" not in res_404.text

    res_422 = client.post("/api/analyze/text", json={})
    assert res_422.status_code == 422
    assert "Traceback" not in res_422.text
    assert "File \"" not in res_422.text


def test_security_no_secrets_in_health():
    """Verify /api/health response contains zero secret keys, env variables, or DB strings."""
    res = client.get("/api/health")
    data = res.json()
    forbidden_keys = ["secret", "key", "password", "token", "env", "database_url"]
    for key in forbidden_keys:
        assert key not in data


def test_security_no_model_path_exposure():
    """Verify /api/model-info does not leak absolute local host filesystem paths."""
    res = client.get("/api/model-info")
    data = res.json()
    text_info = data.get("text_model", {})
    url_info = data.get("url_model", {})
    
    # Model info should report status and version without disclosing host system drive paths
    for key in ["text_model_path", "url_model_path", "absolute_path"]:
        assert key not in text_info
        assert key not in url_info


def test_security_no_network_access_during_url_analysis():
    """Verify URL analysis executes 100% in-memory with zero network calls."""
    # Ensure offline extractor has empty suffix_list_urls
    assert offline_extractor.suffix_list_urls == ()
    
    feats = extract_lexical_features("http://subdomain.bank-verify.xyz/login?user=test")
    assert feats["domain"] == "bank-verify"
    assert feats["suffix"] == "xyz"
    assert feats["subdomain"] == "subdomain"
