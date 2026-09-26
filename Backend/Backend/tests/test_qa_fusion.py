"""QA Automated Test Suite - Risk Fusion Engine Scenarios."""

import pytest
from app.schemas.analyze import (
    RiskLevel,
    RulesEngineResult,
    TextAnalysisResponse,
    UrlAnalysisResponse,
)
from app.services.risk_fusion import RiskFusionService, fuse_risk


def test_fusion_scenario_text_only():
    """Text input present, URL results empty."""
    text_res = TextAnalysisResponse(
        text="Your account is suspended. Share OTP now.",
        risk_score=0.85,
        risk_level=RiskLevel.HIGH_RISK,
        category="credential_harvesting",
        confidence=0.95,
        reasons=["Demands OTP"],
        indicators=["otp_request"],
        model_status="active",
        rules_triggered=["RULE_OTP_REQUEST"],
        extracted_urls=[],
        recommended_action="Do not provide credentials",
    )
    res = fuse_risk(text_result=text_res, url_result=[])
    assert res.final_risk_score > 0.60
    assert res.final_risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_fusion_scenario_url_only():
    """URL input present, Text result missing."""
    url_res = UrlAnalysisResponse(
        url="http://192.168.1.1/login",
        risk_score=0.90,
        risk_level=RiskLevel.HIGH_RISK,
        hostname="192.168.1.1",
        registered_domain="192.168.1.1",
        confidence=0.90,
        model_status="unavailable",
        extracted_features={"is_ip_host": True},
        triggered_rules=["RULE_IP_HOST"],
    )
    res = fuse_risk(text_result=None, url_result=[url_res])
    assert res.final_risk_score > 0.50
    assert res.final_risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_fusion_scenario_combined():
    """Both Text and URL inputs available."""
    text_res = TextAnalysisResponse(
        text="Urgent payment required.",
        risk_score=0.60,
        risk_level=RiskLevel.SUSPICIOUS,
        category="urgency_coercion",
        confidence=0.85,
        reasons=["Urgency demand"],
        indicators=["urgency"],
        model_status="active",
        rules_triggered=["RULE_URGENCY_PAYMENT"],
        extracted_urls=["http://phishing.xyz"],
        recommended_action="Verify independently",
    )
    url_res = UrlAnalysisResponse(
        url="http://phishing.xyz",
        risk_score=0.75,
        risk_level=RiskLevel.SUSPICIOUS,
        hostname="phishing.xyz",
        registered_domain="phishing.xyz",
        confidence=0.85,
        model_status="unavailable",
        extracted_features={"has_suspicious_tld": True},
        triggered_rules=["RULE_SUSPICIOUS_URL"],
    )
    res = fuse_risk(text_result=text_res, url_result=[url_res])
    assert res.final_risk_score >= 0.60


def test_fusion_scenario_missing_model():
    """Missing ML model adapter gracefully falls back to rules and lexical features."""
    rules_res = RulesEngineResult(score=0.40, matched_rules=[])
    res = fuse_risk(text_result=None, url_result=[], rules_result=rules_res)
    assert 0.0 <= res.final_risk_score <= 1.0


def test_fusion_scenario_weak_signals():
    """Low risk / benign inputs produce LOW risk level."""
    text_res = TextAnalysisResponse(
        text="Hello world",
        risk_score=0.05,
        risk_level=RiskLevel.LOW,
        category="benign",
        confidence=0.95,
        reasons=[],
        indicators=[],
        model_status="active",
        rules_triggered=[],
        extracted_urls=[],
        recommended_action="Continue normally",
    )
    res = fuse_risk(text_result=text_res, url_result=[])
    assert res.final_risk_level == RiskLevel.LOW
    assert res.final_risk_score <= 0.29


def test_fusion_scenario_strong_signals():
    """High risk inputs produce HIGH_RISK risk level."""
    text_res = TextAnalysisResponse(
        text="Share your OTP 123456 now.",
        risk_score=0.95,
        risk_level=RiskLevel.HIGH_RISK,
        category="credential_harvesting",
        confidence=0.95,
        reasons=["OTP solicitation"],
        indicators=["otp_solicitation"],
        model_status="active",
        rules_triggered=["RULE_OTP_REQUEST"],
        extracted_urls=[],
        recommended_action="Do not share OTP",
    )
    res = fuse_risk(text_result=text_res, url_result=[])
    assert res.final_risk_level == RiskLevel.HIGH_RISK


def test_fusion_scenario_critical_escalation():
    """Critical rule trigger (OTP request, IP host, remote access) escalates risk level."""
    text_res = TextAnalysisResponse(
        text="Install AnyDesk and share code",
        risk_score=0.40,
        risk_level=RiskLevel.VERIFY_INDEPENDENTLY,
        category="urgency_coercion",
        confidence=0.85,
        reasons=["Remote access"],
        indicators=["remote_access"],
        model_status="active",
        rules_triggered=["RULE_REMOTE_ACCESS"],
        extracted_urls=[],
        recommended_action="Verify independently",
    )
    res = fuse_risk(text_result=text_res, url_result=[])
    assert res.final_risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_fusion_scenario_conflicting_signals():
    """Conflicting signals (e.g., benign text + suspicious URL)."""
    text_res = TextAnalysisResponse(
        text="Thanks for your email.",
        risk_score=0.0,
        risk_level=RiskLevel.LOW,
        category="benign",
        confidence=0.95,
        reasons=[],
        indicators=[],
        model_status="active",
        rules_triggered=[],
        extracted_urls=["http://10.0.0.1/admin"],
        recommended_action="Continue normally",
    )
    url_res = UrlAnalysisResponse(
        url="http://10.0.0.1/admin",
        risk_score=0.85,
        risk_level=RiskLevel.HIGH_RISK,
        hostname="10.0.0.1",
        registered_domain="10.0.0.1",
        confidence=0.90,
        model_status="unavailable",
        extracted_features={"is_ip_host": True},
        triggered_rules=["RULE_IP_HOST"],
    )
    res = fuse_risk(text_result=text_res, url_result=[url_res])
    assert res.final_risk_score > 0.20


def test_fusion_scenario_invalid_score_bounds():
    """Ensure fused risk score is strictly bounded between 0.00 and 1.00."""
    text_res = TextAnalysisResponse(
        text="Test",
        risk_score=1.0,
        risk_level=RiskLevel.HIGH_RISK,
        category="scam",
        confidence=0.95,
        reasons=[],
        indicators=[],
        model_status="active",
        rules_triggered=[],
        extracted_urls=[],
        recommended_action="Caution",
    )
    res = fuse_risk(text_result=text_res, url_result=[])
    assert 0.0 <= res.final_risk_score <= 1.0


def test_fusion_scenario_custom_weights(monkeypatch):
    """Test fusion service initialization and operation with customized weights."""
    fusion_svc = RiskFusionService()
    fusion_svc.text_weight = 0.50
    fusion_svc.url_weight = 0.30
    fusion_svc.rule_weight = 0.20

    text_res = TextAnalysisResponse(
        text="Test message",
        risk_score=0.80,
        risk_level=RiskLevel.HIGH_RISK,
        category="scam",
        confidence=0.90,
        reasons=[],
        indicators=[],
        model_status="active",
        rules_triggered=[],
        extracted_urls=[],
        recommended_action="Block",
    )
    res = fusion_svc.fuse(text_result=text_res, url_results=[])
    assert 0.0 <= res.final_risk_score <= 1.0
