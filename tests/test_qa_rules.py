"""QA Automated Test Suite - Explainable Rules Engine (Positive, Negative, Edge Cases)."""

import pytest
from app.services.rules_engine import evaluate_rules


# 1. RULE_OTP_REQUEST
def test_rule_otp_request_positive():
    """Positive: Explicit OTP solicitation."""
    res = evaluate_rules(text="Please share your OTP with our executive.")
    assert any(m.rule_id == "RULE_OTP_REQUEST" for m in res.matched_rules)


def test_rule_otp_request_negative():
    """Negative: Safe security advisory NOT to share OTP."""
    res = evaluate_rules(text="Your OTP is 456789. Do not share your OTP with anyone.")
    assert not any(m.rule_id == "RULE_OTP_REQUEST" for m in res.matched_rules)


def test_rule_otp_request_edge_case():
    """Edge Case: Case variations, spaces in 'one time password'."""
    res = evaluate_rules(text="Please send me your one time password immediately.")
    assert any(m.rule_id == "RULE_OTP_REQUEST" for m in res.matched_rules)


# 2. RULE_REMOTE_ACCESS
def test_rule_remote_access_positive():
    """Positive: Requesting remote access tool installation."""
    res = evaluate_rules(text="Install AnyDesk and give us remote access to fix your account.")
    assert any(m.rule_id == "RULE_REMOTE_ACCESS" for m in res.matched_rules)


def test_rule_remote_access_negative():
    """Negative: General software discussion without remote access request."""
    res = evaluate_rules(text="We are developing a new desktop application for Windows.")
    assert not any(m.rule_id == "RULE_REMOTE_ACCESS" for m in res.matched_rules)


def test_rule_remote_access_edge_case():
    """Edge Case: Mentioning TeamViewer / QuickSupport in lowercase/uppercase."""
    res = evaluate_rules(text="download teamviewer for support")
    assert any(m.rule_id == "RULE_REMOTE_ACCESS" for m in res.matched_rules)


# 3. RULE_ACCOUNT_THREAT
def test_rule_account_threat_positive():
    """Positive: Threatening immediate account suspension or card blocking."""
    res = evaluate_rules(text="Your SBI card has been suspended due to pending verification.")
    assert any(m.rule_id == "RULE_ACCOUNT_THREAT" for m in res.matched_rules)


def test_rule_account_threat_negative():
    """Negative: Routine account statement or confirmation."""
    res = evaluate_rules(text="Your account statement for August is available for download.")
    assert not any(m.rule_id == "RULE_ACCOUNT_THREAT" for m in res.matched_rules)


def test_rule_account_threat_edge_case():
    """Edge Case: Electricity supply cut / SIM card deactivation threat."""
    res = evaluate_rules(text="Your electricity supply will be disconnected today.")
    assert any(m.rule_id == "RULE_ACCOUNT_THREAT" for m in res.matched_rules)


# 4. RULE_URGENCY_PAYMENT
def test_rule_urgency_payment_positive():
    """Positive: Urgent payment / fine settlement demand within 24 hours."""
    res = evaluate_rules(text="URGENT: Pay your pending penalty fee within 24 hours.")
    assert any(m.rule_id == "RULE_URGENCY_PAYMENT" for m in res.matched_rules)


def test_rule_urgency_payment_negative():
    """Negative: General non-urgent receipt."""
    res = evaluate_rules(text="Thank you for your payment of $50. Here is your receipt.")
    assert not any(m.rule_id == "RULE_URGENCY_PAYMENT" for m in res.matched_rules)


def test_rule_urgency_payment_edge_case():
    """Edge Case: Coercive urgency separated by text block."""
    res = evaluate_rules(text="Action required today: please complete the bill transfer.")
    assert any(m.rule_id == "RULE_URGENCY_PAYMENT" for m in res.matched_rules)


# 5. RULE_SUSPICIOUS_URL
def test_rule_suspicious_url_positive():
    """Positive: High-abuse top-level domain (.xyz, .top, .work)."""
    res = evaluate_rules(url="http://bank-login.top/verify")
    assert any(m.rule_id == "RULE_SUSPICIOUS_URL" for m in res.matched_rules)


def test_rule_suspicious_url_negative():
    """Negative: Legitimate standard TLD (.com, .org, .edu)."""
    res = evaluate_rules(url="https://www.wikipedia.org/wiki/Main_Page")
    assert not any(m.rule_id == "RULE_SUSPICIOUS_URL" for m in res.matched_rules)


def test_rule_suspicious_url_edge_case():
    """Edge Case: Compound TLD or subdomain on suspicious TLD."""
    res = evaluate_rules(url="http://portal.account.xyz")
    assert any(m.rule_id == "RULE_SUSPICIOUS_URL" for m in res.matched_rules)


# 6. RULE_BRAND_DOMAIN_MISMATCH
def test_rule_brand_domain_mismatch_positive():
    """Positive: Claiming SBI brand in subdomain or path of untrusted domain."""
    res = evaluate_rules(url="http://sbi.verify-portal.top/login")
    assert any(m.rule_id == "RULE_BRAND_DOMAIN_MISMATCH" for m in res.matched_rules)


def test_rule_brand_domain_mismatch_negative():
    """Negative: Claiming SBI brand on official sbi.co.in domain."""
    res = evaluate_rules(url="https://onlinesbi.sbi/login")
    assert not any(m.rule_id == "RULE_BRAND_DOMAIN_MISMATCH" for m in res.matched_rules)


def test_rule_brand_domain_mismatch_edge_case():
    """Edge Case: Brand mentioned in path of unrelated domain."""
    res = evaluate_rules(url="https://phishing-portal.com/hdfc/login")
    assert any(m.rule_id == "RULE_BRAND_DOMAIN_MISMATCH" for m in res.matched_rules)


# 7. RULE_IP_HOST
def test_rule_ip_host_positive():
    """Positive: Host is raw IPv4 address."""
    res = evaluate_rules(url="http://192.168.1.50/index.html")
    assert any(m.rule_id == "RULE_IP_HOST" for m in res.matched_rules)


def test_rule_ip_host_negative():
    """Negative: Host is standard domain name."""
    res = evaluate_rules(url="https://example.com/index.html")
    assert not any(m.rule_id == "RULE_IP_HOST" for m in res.matched_rules)


def test_rule_ip_host_edge_case():
    """Edge Case: Bracketed IPv6 host address."""
    res = evaluate_rules(url="http://[::1]:8080/admin")
    assert any(m.rule_id == "RULE_IP_HOST" for m in res.matched_rules)


# 8. RULE_AT_DECEPTION
def test_rule_at_deception_positive():
    """Positive: Authority contains @ sign to obscure true host."""
    res = evaluate_rules(url="https://paypal.com@attacker-site.com/login")
    assert any(m.rule_id == "RULE_AT_DECEPTION" for m in res.matched_rules)


def test_rule_at_deception_negative():
    """Negative: Normal URL without @ sign."""
    res = evaluate_rules(url="https://paypal.com/signin")
    assert not any(m.rule_id == "RULE_AT_DECEPTION" for m in res.matched_rules)


def test_rule_at_deception_edge_case():
    """Edge Case: URL with encoded credentials or userinfo."""
    res = evaluate_rules(url="http://admin:secret@malicious-host.com/")
    assert any(m.rule_id == "RULE_AT_DECEPTION" for m in res.matched_rules)


# 9. CORR_SHORTENER_URGENT_MSG
def test_rule_correlation_positive():
    """Positive: Shortened URL combined with urgent message lure."""
    res = evaluate_rules(
        text="URGENT: Your account is blocked. Update at link immediately.",
        url="https://bit.ly/3xYz91",
    )
    assert any(m.rule_id == "CORR_SHORTENER_URGENT_MSG" for m in res.matched_rules)


def test_rule_correlation_negative():
    """Negative: Shortened URL with calm benign message."""
    res = evaluate_rules(
        text="Here is the link to the meeting notes from yesterday.",
        url="https://bit.ly/3xYz91",
    )
    assert not any(m.rule_id == "CORR_SHORTENER_URGENT_MSG" for m in res.matched_rules)


def test_rule_correlation_edge_case():
    """Edge Case: Full domain URL (non-shortener) with urgent message."""
    res = evaluate_rules(
        text="URGENT: Update your account details.",
        url="https://official-bank.com/update",
    )
    assert not any(m.rule_id == "CORR_SHORTENER_URGENT_MSG" for m in res.matched_rules)
