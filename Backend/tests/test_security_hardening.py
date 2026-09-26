import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.limiter import limiter
from app.main import create_application
from app.services.url_extractor import extract_urls
from app.utils.url_utils import offline_extractor


def patch_settings(monkeypatch, custom_settings: Settings):
    """Helper to clear lru_cache and patch get_settings across all app modules."""
    get_settings.cache_clear()
    monkeypatch.setattr("app.core.config.get_settings", lambda: custom_settings)
    monkeypatch.setattr("app.main.get_settings", lambda: custom_settings)
    monkeypatch.setattr("app.api.routes.analyze.get_settings", lambda: custom_settings)


# =====================================================================
# A. TLDExtract Offline Hardening Tests
# =====================================================================

def test_tldextract_explicitly_configured_offline():
    """Verify tldextract is strictly configured with empty suffix_list_urls to prevent HTTP/DNS lookups."""
    assert offline_extractor.suffix_list_urls == ()
    
    # Test domain parsing works offline
    res = offline_extractor("https://subdomain.bank-verify.co.uk/path")
    assert res.domain == "bank-verify"
    assert res.suffix == "co.uk"
    assert res.subdomain == "subdomain"


def test_url_extractor_uses_offline_extractor():
    """Verify extract_urls uses centralized offline_extractor without network calls."""
    text = "Visit http://malicious-login.xyz/verify or www.scam-bank.top/login"
    urls = extract_urls(text)
    assert "http://malicious-login.xyz/verify" in urls
    assert "https://www.scam-bank.top/login" in urls


# =====================================================================
# B. API Rate Limiting Tests
# =====================================================================

def test_rate_limiting_enforced_on_analyze_endpoints(monkeypatch):
    """Verify analysis endpoints return HTTP 429 when rate limit is exceeded."""
    test_settings = Settings(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_ANALYZE="2/minute",
        ALLOWED_ORIGINS=["http://testserver"],
    )
    patch_settings(monkeypatch, test_settings)
    
    limiter.reset()
    limiter.enabled = True

    app = create_application()
    client = TestClient(app)

    # First two requests should succeed
    res1 = client.post("/api/analyze/text", json={"text": "Test message 1"})
    assert res1.status_code == 200

    res2 = client.post("/api/analyze/text", json={"text": "Test message 2"})
    assert res2.status_code == 200

    # Third request should trigger rate limiting (HTTP 429)
    res3 = client.post("/api/analyze/text", json={"text": "Test message 3"})
    assert res3.status_code == 429

    payload = res3.json()
    assert "error" in payload
    assert payload["error"]["code"] == "TOO_MANY_REQUESTS"
    assert "Rate limit exceeded" in payload["error"]["message"]
    assert "request_id" in payload["error"]

    limiter.reset()


def test_rate_limiting_disabled_when_flag_off(monkeypatch):
    """Verify rate limiting is bypassed when RATE_LIMIT_ENABLED is False."""
    test_settings = Settings(
        RATE_LIMIT_ENABLED=False,
        RATE_LIMIT_ANALYZE="1/minute",
        ALLOWED_ORIGINS=["http://testserver"],
    )
    patch_settings(monkeypatch, test_settings)
    
    limiter.reset()
    app = create_application()
    client = TestClient(app)

    # Multiple requests should succeed since rate limiting is disabled
    res1 = client.post("/api/analyze/text", json={"text": "Test 1"})
    res2 = client.post("/api/analyze/text", json={"text": "Test 2"})
    assert res1.status_code == 200
    assert res2.status_code == 200

    limiter.reset()


def test_health_endpoints_not_blocked_by_rate_limiter(monkeypatch):
    """Verify health endpoints remain accessible without rate limit interference."""
    test_settings = Settings(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_ANALYZE="1/minute",
    )
    patch_settings(monkeypatch, test_settings)
    limiter.reset()

    app = create_application()
    client = TestClient(app)

    # Exhaust analyze limit
    client.post("/api/analyze/text", json={"text": "First message"})
    
    # Health check should still return HTTP 200
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# =====================================================================
# C. Production CORS Hardening Tests
# =====================================================================

def test_production_cors_rejects_wildcard():
    """Verify production mode raises ValueError if ALLOWED_ORIGINS contains wildcard '*'."""
    with pytest.raises(ValueError, match="Wildcard CORS origin '\\*' is strictly prohibited in production mode"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["*"],
        )


def test_production_cors_rejects_empty_origins():
    """Verify production mode raises ValueError if ALLOWED_ORIGINS is empty."""
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS must be explicitly configured in production mode"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=[],
        )


def test_production_cors_rejects_invalid_scheme():
    """Verify production mode raises ValueError if an origin lacks http/https scheme."""
    with pytest.raises(ValueError, match="Invalid CORS origin scheme"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["ftp://malicious.com"],
        )


def test_production_cors_accepts_valid_origins():
    """Verify production mode accepts valid explicit HTTPS/HTTP origins."""
    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS=["https://linksentry.app", "https://admin.linksentry.app"],
    )
    assert settings.ALLOWED_ORIGINS == ["https://linksentry.app", "https://admin.linksentry.app"]


def test_cors_middleware_allowed_and_disallowed_origins(monkeypatch):
    """Verify CORS headers allow configured origin and reject unconfigured origin."""
    test_settings = Settings(
        ENVIRONMENT="development",
        ALLOWED_ORIGINS=["http://allowed-frontend.com"],
    )
    patch_settings(monkeypatch, test_settings)

    app = create_application()
    client = TestClient(app)

    # Request with allowed origin
    res_allowed = client.options(
        "/api/analyze/text",
        headers={
            "Origin": "http://allowed-frontend.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res_allowed.headers.get("access-control-allow-origin") == "http://allowed-frontend.com"

    # Request with unallowed origin
    res_disallowed = client.options(
        "/api/analyze/text",
        headers={
            "Origin": "http://untrusted-attacker.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res_disallowed.headers.get("access-control-allow-origin") is None
