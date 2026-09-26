"""QA Automated Test Suite - Text Analysis Scenarios."""

import pytest
from app.services.model_service import get_model_service

service = get_model_service()


def test_text_scenario_empty():
    res = service.analyze_text_content("")
    assert res.risk_score == 0.0
    assert res.risk_level.value == "low"


def test_text_scenario_whitespace():
    res = service.analyze_text_content("   \n\t   ")
    assert res.risk_score == 0.0
    assert res.risk_level.value == "low"


def test_text_scenario_normal():
    res = service.analyze_text_content("Hey John, let's meet tomorrow at 5 PM for coffee.")
    assert res.risk_score <= 0.29
    assert res.risk_level.value == "low"


def test_text_scenario_legitimate_otp():
    """Legitimate bank advisory telling user NOT to share OTP."""
    text = "Your OTP is 984512 for transaction at Amazon. Do not share this OTP with anyone, including bank officials."
    res = service.analyze_text_content(text)
    assert res.risk_level.value == "low"
    assert "TXT_CREDENTIAL_SOLICITATION" not in res.rules_triggered


def test_text_scenario_otp_theft():
    """Malicious request asking user to provide/share OTP."""
    text = "Dear Customer, please share your OTP 654321 with our support executive to prevent card blocking."
    res = service.analyze_text_content(text)
    assert res.risk_score >= 0.35
    assert "TXT_CREDENTIAL_SOLICITATION" in res.rules_triggered


def test_text_scenario_kyc():
    """KYC update scam lure."""
    text = "IMPORTANT: Your bank KYC document has expired. Update your KYC immediately within 24 hours."
    res = service.analyze_text_content(text)
    assert res.risk_score > 0.0
    assert res.category in ("credential_harvesting", "urgency_coercion", "scam") or len(res.rules_triggered) > 0


def test_text_scenario_payment():
    """Urgent payment or penalty settlement demand."""
    text = "URGENT: Pay your pending electricity bill immediately to avoid power disconnection today."
    res = service.analyze_text_content(text)
    assert "TXT_UTILITY_DISCONNECT" in res.rules_triggered or "TXT_COERCIVE_URGENCY" in res.rules_triggered


def test_text_scenario_account_threat():
    """Threatening account suspension or netbanking block."""
    text = "Your NetBanking account is blocked due to suspicious activity. Click link to unblock."
    res = service.analyze_text_content(text)
    assert "TXT_ACCOUNT_SUSPENSION" in res.rules_triggered or "TXT_URGENT_VERIFICATION" in res.rules_triggered


def test_text_scenario_remote_access():
    """Soliciting installation of remote support apps (AnyDesk, TeamViewer)."""
    text = "Customer Support: Please download AnyDesk software and share your 9-digit code for quick support."
    res = service.analyze_text_content(text)
    assert res.risk_score > 0.0


def test_text_scenario_reward():
    """Lottery reward / gift claim lure."""
    text = "Congratulations! You have won $10,000 lottery reward. Claim your refund and prize now."
    res = service.analyze_text_content(text)
    assert res.risk_score > 0.0
    assert "TXT_FINANCIAL_LURE" in res.rules_triggered


def test_text_scenario_mixed_language():
    """Hinglish / multilingual scam text."""
    text = "Aapka SBI account suspend hone wala hai. Immediately apna OTP 998877 share karein."
    res = service.analyze_text_content(text)
    assert len(res.rules_triggered) > 0


def test_text_scenario_unicode():
    """Text with homoglyphs, non-ASCII Unicode characters."""
    text = "Yоur SВI ассоunt has been blосkеd. Ρlеаsе vеrify immеdiаtеly."
    res = service.analyze_text_content(text)
    assert isinstance(res.risk_score, float)
    assert res.category is not None


def test_text_scenario_emoji():
    """Text heavy with emojis."""
    text = "🚨 URGENT NOTICE 🚨 Your account is blocked 🔒! Share OTP 🔑 immediately ⚡"
    res = service.analyze_text_content(text)
    assert res.risk_score >= 0.20


def test_text_scenario_very_long():
    """Very long message text within max limit bounds."""
    text = "Notification: " + ("Safe corporate email update text. " * 200)
    res = service.analyze_text_content(text)
    assert isinstance(res.risk_score, float)
    assert res.risk_score <= 0.30


def test_text_scenario_multiple_urls():
    """Text payload containing multiple embedded URLs."""
    text = "Check http://benign-site.com and http://phishing-portal.top/login for details."
    res = service.analyze_text_content(text)
    assert len(res.extracted_urls) == 2
    assert "http://benign-site.com" in res.extracted_urls
    assert "http://phishing-portal.top/login" in res.extracted_urls
