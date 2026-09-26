"""QA Automated Test Suite - URL Analysis Scenarios."""

import pytest
from app.services.model_service import get_model_service

service = get_model_service()


def test_url_scenario_https():
    """Standard legitimate HTTPS URL."""
    res = service.analyze_url_content("https://www.google.com/search?q=security")
    assert res.extracted_features["is_https"] is True
    assert res.risk_score <= 0.29


def test_url_scenario_http():
    """Unencrypted HTTP URL."""
    res = service.analyze_url_content("http://example-service.com/login")
    assert res.extracted_features["is_https"] is False


def test_url_scenario_ip_host():
    """Raw IPv4 host address URL."""
    res = service.analyze_url_content("http://192.168.1.100/admin/login")
    assert res.extracted_features["is_ip_host"] is True
    assert "RULE_IP_HOST" in res.triggered_rules
    assert res.risk_level.value in ("suspicious", "high_risk")


def test_url_scenario_localhost():
    """Localhost / loopback address URL."""
    res = service.analyze_url_content("http://localhost:8000/api/docs")
    assert res.extracted_features["is_private_or_loopback_ip"] is True


def test_url_scenario_malformed():
    """Malformed or invalid URL string handling."""
    res = service.analyze_url_content("not_a_valid_url_at_all!#$")
    assert res.risk_score >= 0.0
    assert "url_length" in res.extracted_features


def test_url_scenario_long():
    """Excessively long obfuscated URL."""
    long_path = "a" * 500
    res = service.analyze_url_content(f"https://suspicious-portal.xyz/{long_path}")
    assert res.extracted_features["url_length"] > 500
    assert res.risk_score > 0.30


def test_url_scenario_subdomain_heavy():
    """URL with deep nested subdomains (subdomain spoofing)."""
    res = service.analyze_url_content("https://login.sbi.co.in.verification.portal.xyz/login")
    assert res.extracted_features["subdomain_count"] >= 4
    assert res.extracted_features["has_suspicious_tld"] is True


def test_url_scenario_at_deception():
    """URL containing authority @ sign deception."""
    res = service.analyze_url_content("https://sbi.co.in@evil-phishing.com/login")
    assert res.extracted_features["has_at_deception"] is True
    assert "RULE_AT_DECEPTION" in res.triggered_rules


def test_url_scenario_punycode():
    """Punycode IDN homoglyph domain URL."""
    res = service.analyze_url_content("https://xn--gogl-0nd.com/login")
    assert res.extracted_features["is_punycode"] is True
    assert res.extracted_features["is_idn"] is True


def test_url_scenario_suspicious_keywords():
    """URL with phishing keywords in path."""
    res = service.analyze_url_content("https://account-verify-secure.top/kyc/update")
    assert "login" in res.extracted_features["suspicious_keywords_present"] or \
           "verify" in res.extracted_features["suspicious_keywords_present"] or \
           "kyc" in res.extracted_features["suspicious_keywords_present"] or \
           "update" in res.extracted_features["suspicious_keywords_present"]


def test_url_scenario_shortener():
    """Known URL shortener domain."""
    res = service.analyze_url_content("https://bit.ly/3xYz91")
    assert res.extracted_features["is_shortener"] is True


def test_url_scenario_query_parameters():
    """URL with multiple query parameters."""
    res = service.analyze_url_content("https://target-portal.com/auth?session=12345&token=abcde&redirect=http://test.com")
    assert res.extracted_features["query_param_count"] >= 3
    assert res.extracted_features["query_length"] > 20


def test_url_scenario_unicode():
    """URL containing non-ASCII Unicode characters."""
    res = service.analyze_url_content("https://bank-vèrifý.com/secure")
    assert res.extracted_features["is_idn"] is True
