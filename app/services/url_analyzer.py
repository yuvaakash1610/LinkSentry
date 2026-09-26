from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.core.config import get_settings
from app.ml.base_model import BaseModel
from app.ml.url_model import UrlMLModel
from app.schemas.analyze import RiskLevel, UrlAnalysisResponse
from app.utils.masking import mask_sensitive_url_params
from app.utils.url_utils import extract_lexical_features, is_valid_url, normalize_url


def score_to_risk_level(score: float) -> RiskLevel:
    """Map continuous score [0.0, 1.0] to discrete LinkSentry RiskLevel."""
    if score >= 0.80:
        return RiskLevel.HIGH_RISK
    elif score >= 0.60:
        return RiskLevel.SUSPICIOUS
    elif score >= 0.30:
        return RiskLevel.VERIFY_INDEPENDENTLY
    return RiskLevel.LOW


class UrlAnalyzer:
    """
    Subsystem for static lexical and structural URL string analysis.
    
    CRITICAL SECURITY MANDATE:
    This service operates purely on URL strings. It NEVER executes network requests,
    DNS lookups, redirects, HTML rendering, or socket connections.
    """

    def __init__(self, url_model: Optional[BaseModel] = None) -> None:
        self.url_model = url_model or UrlMLModel()

    def analyze(self, raw_url: str) -> UrlAnalysisResponse:
        settings = get_settings()

        # Step 1: Validate input
        if not raw_url or not raw_url.strip():
            return UrlAnalysisResponse(
                url="",
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                hostname="",
                registered_domain="",
                indicators=[],
                extracted_features={},
                model_prediction=None,
                confidence=0.95,
                model_status="active" if self.url_model.is_available else "unavailable",
                triggered_rules=[],
                claimed_brand=None,
                brand_domain_mismatch=False,
                is_ip_host=False,
                is_shortener=False,
            )

        cleaned_url = raw_url.strip()[: settings.MAX_URL_LENGTH]

        # Step 2: Normalize
        normalized_url = normalize_url(cleaned_url)

        # Step 3: Extract lexical and structural features (100% offline)
        features = extract_lexical_features(normalized_url)

        # Safe masked representation for reporting
        safe_url = mask_sensitive_url_params(normalized_url)

        # Step 4: Deterministic Indicators & Rule Evaluation
        indicators: List[str] = []
        triggered_rules: List[str] = []
        heuristic_score = 0.0

        # Indicator: @ Deception (authority trickery)
        if features["has_at_deception"]:
            indicators.append("at_authority_deception")
            triggered_rules.append("URL_AT_DECEPTION")
            heuristic_score += 0.55

        # Indicator: Raw IP Host (IPv4 / IPv6)
        if features["is_ip_host"]:
            indicators.append("ip_address_host")
            triggered_rules.append("URL_IP_HOST")
            heuristic_score += 0.50

            if features["is_ipv6"]:
                indicators.append("ipv6_host")
            else:
                indicators.append("ipv4_host")

        # Indicator: Localhost / Private / Cloud Metadata IP
        if features["is_private_or_loopback_ip"]:
            indicators.append("private_or_loopback_target")
            triggered_rules.append("URL_PRIVATE_OR_METADATA_TARGET")
            heuristic_score += 0.55

        # Indicator: Brand Domain Mismatch (e.g. paypal in path/subdomain on attacker domain)
        if features["brand_domain_mismatch"]:
            indicators.append("brand_domain_mismatch")
            triggered_rules.append("URL_BRAND_MISMATCH")
            heuristic_score += 0.55

        # Indicator: Suspicious / High-Abuse TLD (.xyz, .top, .buzz, etc.)
        if features["has_suspicious_tld"]:
            indicators.append("suspicious_tld")
            triggered_rules.append("URL_SUSPICIOUS_TLD")
            heuristic_score += 0.35

        # Indicator: Punycode / IDN
        if features["is_punycode"]:
            indicators.append("punycode_homoglyph")
            triggered_rules.append("URL_PUNYCODE_HOMOGLYPH")
            heuristic_score += 0.35
        elif features["is_idn"]:
            indicators.append("unicode_idn")

        # Indicator: URL Shortener
        if features["is_shortener"]:
            indicators.append("url_shortener")
            triggered_rules.append("URL_SHORTENER")
            heuristic_score += 0.20

        # Indicator: Excessive Subdomains
        if features["subdomain_count"] >= 3:
            indicators.append("excessive_subdomains")
            triggered_rules.append("URL_DEEP_SUBDOMAINS")
            heuristic_score += 0.25

        # Indicator: Unencrypted HTTP Scheme
        if not features["is_https"]:
            indicators.append("http_unencrypted")
            triggered_rules.append("URL_HTTP_INSECURE")
            heuristic_score += 0.15

        # Indicator: Excessive Length
        if features["url_length"] > 150:
            indicators.append("excessive_length")
            heuristic_score += 0.15

        # Indicator: Query Heavy
        if features["query_param_count"] >= 5 or features["query_length"] > 100:
            indicators.append("query_heavy")

        # Suspicious keywords presence:
        found_kw = features.get("suspicious_keywords_present", [])
        if found_kw:
            indicators.append("suspicious_keywords")
            if heuristic_score > 0.15:
                heuristic_score += min(0.20, len(found_kw) * 0.05)
                triggered_rules.append("URL_SUSPICIOUS_KEYWORDS")

        heuristic_score = min(1.0, heuristic_score)

        # Step 5: Machine Learning Adapter (if real artifact is provided)
        ml_score, is_model_available = self.url_model.predict(features)

        if is_model_available and ml_score is not None:
            final_score = round(0.70 * ml_score + 0.30 * heuristic_score, 4)
            confidence = 0.88
            model_status = "active"
            model_prediction = ml_score
        else:
            final_score = round(heuristic_score, 4)
            confidence = 0.85 if indicators else 0.95
            model_status = "unavailable"
            model_prediction = None

        risk_level = score_to_risk_level(final_score)

        # Step 6: Construct Typed Result
        return UrlAnalysisResponse(
            url=safe_url,
            risk_score=final_score,
            risk_level=risk_level,
            hostname=features["hostname"],
            registered_domain=features["registered_domain"],
            indicators=indicators,
            extracted_features=features,
            model_prediction=model_prediction,
            confidence=confidence,
            model_status=model_status,
            triggered_rules=triggered_rules,
            claimed_brand=features["claimed_brand"],
            brand_domain_mismatch=features["brand_domain_mismatch"],
            is_ip_host=features["is_ip_host"],
            is_shortener=features["is_shortener"],
        )
