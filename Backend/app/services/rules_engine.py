import re
from typing import Any, Dict, List, Optional
from app.schemas.analyze import RuleMatch, RulesEngineResult
from app.utils.url_utils import extract_lexical_features


def _check_otp_solicitation(text: str) -> bool:
    """Detect solicitation of OTP while excluding benign security advisories."""
    cleaned = re.sub(
        r"\b(?:do\s*not|never|don't)\s+(?:share|disclose|give)\s+(?:your\s+|this\s+)?(?:otp|pin|password|code)\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return bool(
        re.search(
            r"\b(?:send|share|give|provide|forward|tell|enter)\s+(?:me\s+|us\s+)?(?:your\s+|the\s+)?(?:otp|one\s*time\s*password|pin|cvv|credentials?)\b",
            cleaned,
            re.IGNORECASE,
        )
    )


RULES_CONFIG = {
    # Text rules
    "RULE_OTP_REQUEST": {
        "id": "RULE_OTP_REQUEST",
        "description": "Solicitation for OTP or credentials from the user",
        "weight": 35,
        "severity": "HIGH",
        "evidence_type": "text",
        "condition": _check_otp_solicitation,
        "reason": lambda txt: "Message prompts user to share or provide sensitive OTP or verification credentials",
    },
    "RULE_REMOTE_ACCESS": {
        "id": "RULE_REMOTE_ACCESS",
        "description": "Requests remote access software or device control",
        "weight": 30,
        "severity": "HIGH",
        "evidence_type": "text",
        "condition": lambda txt: bool(
            re.search(
                r"\b(?:remote\s+(?:access|control|support)|anydesk|teamviewer|quicksupport|ultraviewer|rustdesk|install\s+(?:remote|support\s+app))\b",
                txt,
                re.IGNORECASE,
            )
        ),
        "reason": lambda txt: "Message requests remote device control or unauthorized application installation",
    },
    "RULE_ACCOUNT_THREAT": {
        "id": "RULE_ACCOUNT_THREAT",
        "description": "Threatens account suspension, deactivation, or blocking",
        "weight": 20,
        "severity": "MEDIUM",
        "evidence_type": "text",
        "condition": lambda txt: bool(
            re.search(
                r"\b(?:account|profile|netbanking|card|sim|service|electricity|supply)\s+(?:is\s+|will\s+be\s+|has\s+been\s+)?(?:blocked|suspended|deactivated|frozen|closed|terminated|locked|disconnected|cut)\b",
                txt,
                re.IGNORECASE,
            )
        ),
        "reason": lambda txt: "Message threatens account suspension or immediate service disruption",
    },
    "RULE_URGENCY_PAYMENT": {
        "id": "RULE_URGENCY_PAYMENT",
        "description": "Urgent request for payment, transfer, or penalty settlement",
        "weight": 15,
        "severity": "HIGH",
        "evidence_type": "text",
        "condition": lambda txt: bool(
            re.search(
                r"\b(?:urgent|immediately|within\s*24\s*hours?|action\s*required|today)\b.*?\b(?:pay|payment|transfer|send\s*money|bill|penalty|fine)\b|\b(?:pay|transfer|send\s*money|bill|penalty|fine)\b.*?\b(?:urgent|immediately|within\s*24\s*hours?|action\s*required|today)\b",
                txt,
                re.IGNORECASE | re.DOTALL,
            )
        ),
        "reason": lambda txt: "Coercive urgency pressure linked to immediate financial payment",
    },
    # URL rules
    "RULE_SUSPICIOUS_URL": {
        "id": "RULE_SUSPICIOUS_URL",
        "description": "URL uses a suspicious or known high-abuse top-level domain",
        "weight": 15,
        "severity": "HIGH",
        "evidence_type": "url",
        "condition": lambda feats: bool(feats.get("has_suspicious_tld")),
        "reason": lambda feats: f"URL uses suspicious or high-abuse TLD .{feats.get('suffix', '')}",
    },
    "RULE_BRAND_DOMAIN_MISMATCH": {
        "id": "RULE_BRAND_DOMAIN_MISMATCH",
        "description": "Target brand name mentioned but domain does not match official brand",
        "weight": 20,
        "severity": "HIGH",
        "evidence_type": "url",
        "condition": lambda feats: bool(feats.get("brand_domain_mismatch")),
        "reason": lambda feats: f"Brand '{feats.get('claimed_brand')}' targeted without matching registered domain",
    },
    "RULE_IP_HOST": {
        "id": "RULE_IP_HOST",
        "description": "URL host is a raw numeric IP address",
        "weight": 25,
        "severity": "CRITICAL",
        "evidence_type": "url",
        "condition": lambda feats: bool(feats.get("is_ip_host") or feats.get("is_ip_address")),
        "reason": lambda feats: "Target host uses raw IP address instead of legitimate domain",
    },
    "RULE_AT_DECEPTION": {
        "id": "RULE_AT_DECEPTION",
        "description": "URL contains '@' symbol to obfuscate true host destination",
        "weight": 20,
        "severity": "HIGH",
        "evidence_type": "url",
        "condition": lambda feats: bool(feats.get("has_at_deception") or feats.get("count_at_signs", 0) > 0),
        "reason": lambda feats: "URL contains '@' authority deception to hide real destination",
    },
}


def evaluate_rules(
    text: Optional[str] = None,
    url: Optional[str] = None,
    url_features: Optional[Dict[str, Any]] = None,
) -> RulesEngineResult:
    """Evaluate all configurable deterministic rules and return explainable matches."""
    matched: List[RuleMatch] = []
    raw_score = 0.0

    # 1. Text rules
    if text:
        for cfg in RULES_CONFIG.values():
            if cfg["evidence_type"] != "text":
                continue
            cond = cfg.get("condition")
            if cond and cond(text):
                norm = min(1.0, cfg["weight"] / 100.0)
                matched.append(
                    RuleMatch(
                        rule_id=cfg["id"],
                        description=cfg["description"],
                        severity=cfg["severity"],
                        weight=cfg["weight"],
                        score=round(norm, 4),
                        reason=cfg["reason"](text),
                        evidence_type=cfg["evidence_type"],
                    )
                )
                raw_score += cfg["weight"]

    # 2. URL rules
    if url:
        feats = url_features or extract_lexical_features(url)
        for cfg in RULES_CONFIG.values():
            if cfg["evidence_type"] != "url":
                continue
            cond = cfg.get("condition")
            if cond and cond(feats):
                norm = min(1.0, cfg["weight"] / 100.0)
                matched.append(
                    RuleMatch(
                        rule_id=cfg["id"],
                        description=cfg["description"],
                        severity=cfg["severity"],
                        weight=cfg["weight"],
                        score=round(norm, 4),
                        reason=cfg["reason"](feats),
                        evidence_type=cfg["evidence_type"],
                    )
                )
                raw_score += cfg["weight"]

    # 3. Correlation rule (shortener + urgent text)
    if text and url:
        feats = url_features or extract_lexical_features(url)
        if feats.get("is_shortener") and any(m.evidence_type == "text" for m in matched):
            weight = 30
            norm = min(1.0, weight / 100.0)
            matched.append(
                RuleMatch(
                    rule_id="CORR_SHORTENER_URGENT_MSG",
                    description="URL shortener combined with urgent/financial lure conceals destination.",
                    severity="HIGH",
                    weight=weight,
                    score=round(norm, 4),
                    reason="Shortened URL appears in combination with urgent text lure",
                    evidence_type="combined",
                )
            )
            raw_score += weight

    # Normalized overall heuristic score (0.0 to 1.0)
    normalized_score = round(min(1.0, raw_score / 100.0), 4)
    return RulesEngineResult(score=normalized_score, matched_rules=matched)
