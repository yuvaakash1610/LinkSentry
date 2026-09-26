import socket
import urllib.request
import httpx
import pytest
from app.schemas.analyze import RiskLevel
from app.services.url_analyzer import UrlAnalyzer
from app.utils.url_utils import extract_lexical_features, is_valid_url


@pytest.fixture
def analyzer() -> UrlAnalyzer:
    return UrlAnalyzer()


# --- CRITICAL TEST: PROVE ZERO NETWORK CALLS ---

def test_critical_security_no_network_calls_performed(analyzer: UrlAnalyzer, monkeypatch):
    """
    MANDATORY CRITICAL TEST:
    Prove beyond doubt that URL analysis operates 100% on static strings
    and never initiates network calls, DNS lookups, or socket connections.
    """
    def forbidden_network_call(*args, **kwargs):
        raise AssertionError("SECURITY VIOLATION: Network call was attempted during URL analysis!")

    # Patch socket creation and connection
    monkeypatch.setattr(socket, "getaddrinfo", forbidden_network_call)
    monkeypatch.setattr(socket, "gethostbyname", forbidden_network_call)
    monkeypatch.setattr(socket.socket, "connect", forbidden_network_call)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden_network_call)
    monkeypatch.setattr(httpx.Client, "send", forbidden_network_call)

    # Test an array of diverse and potentially dangerous URLs
    test_urls = [
        "https://www.google.com/search?q=test",
        "http://192.168.1.1:8080/admin",
        "http://[2001:db8::1]/path",
        "https://bank.example@attacker.xyz/login",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/api",
        "https://bit.ly/malicious-link",
        "https://xn--pple-43d.com/secure",
    ]

    for test_url in test_urls:
        result = analyzer.analyze(test_url)
        assert result is not None
        assert 0.0 <= result.risk_score <= 1.0


# --- FUNCTIONAL TESTS FOR ALL URL CATEGORIES ---

def test_url_normal_https(analyzer: UrlAnalyzer):
    url = "https://www.wikipedia.org/wiki/Computer_security"
    result = analyzer.analyze(url)

    assert result.risk_level == RiskLevel.LOW
    assert result.risk_score < 0.25
    assert result.extracted_features["is_https"] is True
    assert result.extracted_features["is_ip_host"] is False
    assert result.registered_domain == "wikipedia.org"


def test_url_unencrypted_http(analyzer: UrlAnalyzer):
    url = "http://example.com/public-info"
    result = analyzer.analyze(url)

    assert result.extracted_features["is_https"] is False
    assert "http_unencrypted" in result.indicators
    assert "URL_HTTP_INSECURE" in result.triggered_rules


def test_url_ipv4_host(analyzer: UrlAnalyzer):
    url = "http://198.51.100.12/verify-account"
    result = analyzer.analyze(url)

    assert result.is_ip_host is True
    assert result.extracted_features["is_ipv4"] is True
    assert result.extracted_features["is_ipv6"] is False
    assert "ip_address_host" in result.indicators
    assert result.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_url_ipv6_host(analyzer: UrlAnalyzer):
    url = "http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:8080/login"
    result = analyzer.analyze(url)

    assert result.is_ip_host is True
    assert result.extracted_features["is_ipv6"] is True
    assert "ipv6_host" in result.indicators
    assert result.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_url_localhost_and_private_addresses(analyzer: UrlAnalyzer):
    urls = [
        "http://localhost:3000/dashboard",
        "http://127.0.0.1:8000/secret",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/admin",
    ]
    for url in urls:
        result = analyzer.analyze(url)
        assert result.extracted_features["is_private_or_loopback_ip"] is True
        assert "private_or_loopback_target" in result.indicators
        assert "URL_PRIVATE_OR_METADATA_TARGET" in result.triggered_rules
        assert result.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_url_at_deception(analyzer: UrlAnalyzer):
    # User sees trusted.example, but browser connects to evil.example
    url = "https://trusted.example@evil.example/login"
    result = analyzer.analyze(url)

    assert result.extracted_features["has_at_deception"] is True
    assert result.hostname == "evil.example"
    assert "at_authority_deception" in result.indicators
    assert "URL_AT_DECEPTION" in result.triggered_rules
    assert result.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_url_brand_domain_mismatch(analyzer: UrlAnalyzer):
    # Legitimate brand name 'paypal' used in path or subdomain of attacker domain
    phishing_url = "https://paypal.verification-portal.xyz/login"
    result = analyzer.analyze(phishing_url)

    assert result.claimed_brand == "paypal"
    assert result.brand_domain_mismatch is True
    assert "brand_domain_mismatch" in result.indicators
    assert "URL_BRAND_MISMATCH" in result.triggered_rules
    assert result.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)

    # Legitimate official brand domain must NOT trigger mismatch
    legit_url = "https://www.paypal.com/signin"
    legit_result = analyzer.analyze(legit_url)
    assert legit_result.claimed_brand == "paypal"
    assert legit_result.brand_domain_mismatch is False
    assert "brand_domain_mismatch" not in legit_result.indicators


def test_url_suspicious_keywords_do_not_automatically_flag_benign():
    # Keywords like 'login' on standard HTTPS legitimate domain
    analyzer = UrlAnalyzer()
    benign_url = "https://accounts.google.com/login"
    result = analyzer.analyze(benign_url)

    assert "login" in result.extracted_features["suspicious_keywords_present"]
    # MUST NOT automatically be flagged malicious
    assert result.risk_level == RiskLevel.LOW
    assert result.risk_score < 0.25


def test_url_many_subdomains(analyzer: UrlAnalyzer):
    url = "https://deep.nested.subdomain.layers.example.com/portal"
    result = analyzer.analyze(url)

    assert result.extracted_features["subdomain_count"] >= 4
    assert "excessive_subdomains" in result.indicators
    assert "URL_DEEP_SUBDOMAINS" in result.triggered_rules


def test_url_punycode_and_unicode(analyzer: UrlAnalyzer):
    # Punycode spoofing apple
    punycode_url = "https://xn--pple-43d.com/support"
    result = analyzer.analyze(punycode_url)

    assert result.extracted_features["is_punycode"] is True
    assert "punycode_homoglyph" in result.indicators

    # Unicode Cyrillic URL
    unicode_url = "https://президент.рф/документы"
    result_uni = analyzer.analyze(unicode_url)
    assert result_uni.extracted_features["is_idn"] is True


def test_url_shortener(analyzer: UrlAnalyzer):
    url = "https://bit.ly/3gHjKl"
    result = analyzer.analyze(url)

    assert result.is_shortener is True
    assert "url_shortener" in result.indicators
    assert "URL_SHORTENER" in result.triggered_rules


def test_url_long_and_query_heavy(analyzer: UrlAnalyzer):
    # Build long, query-heavy URL
    base = "https://example.com/search?"
    params = "&".join(f"param{i}=value{i}_extra_long_payload_padding" for i in range(10))
    long_query_url = base + params
    result = analyzer.analyze(long_query_url)

    assert result.extracted_features["url_length"] > 150
    assert result.extracted_features["query_param_count"] == 10
    assert "excessive_length" in result.indicators
    assert "query_heavy" in result.indicators


def test_url_malformed_and_empty(analyzer: UrlAnalyzer):
    # Empty string
    empty_result = analyzer.analyze("")
    assert empty_result.risk_level == RiskLevel.LOW
    assert empty_result.url == ""

    # Malformed URL string
    malformed = "   not-a-valid-url   "
    res = analyzer.analyze(malformed)
    assert res is not None
    assert 0.0 <= res.risk_score <= 1.0


def test_all_extracted_features_schema_completeness(analyzer: UrlAnalyzer):
    url = "https://sub.portal.xyz/login?token=abc#section"
    features = extract_lexical_features(url)

    required_keys = [
        "url_length",
        "hostname_length",
        "registered_domain_length",
        "path_length",
        "query_length",
        "fragment_length",
        "dot_count",
        "hyphen_count",
        "underscore_count",
        "slash_count",
        "at_count",
        "question_count",
        "equal_count",
        "ampersand_count",
        "percent_count",
        "digit_count",
        "subdomain_count",
        "path_depth",
        "scheme",
        "is_https",
        "is_ip_host",
        "is_ipv4",
        "is_ipv6",
        "is_private_or_loopback_ip",
        "has_at_deception",
        "is_punycode",
        "is_idn",
        "is_shortener",
        "has_suspicious_tld",
        "hostname_entropy",
        "url_entropy",
        "query_param_count",
        "suspicious_keywords_present",
        "claimed_brand",
        "brand_domain_mismatch",
    ]

    for key in required_keys:
        assert key in features, f"Missing required feature key: '{key}'"
