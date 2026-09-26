import re
from typing import List, Optional, Tuple
from app.ml.base_model import BaseModel
from app.ml.text_model import TextMLModel
from app.schemas.analyze import RiskLevel, TextAnalysisResponse
from app.services.url_extractor import extract_urls

# Standard recommended action advisories per LinkSentry PRD
RECOMMENDED_ACTIONS = {
    RiskLevel.LOW: "Continue normally, while remaining cautious.",
    RiskLevel.VERIFY_INDEPENDENTLY: "Verify the request using an official source before taking action.",
    RiskLevel.SUSPICIOUS: "Do not provide sensitive information or make a payment until independently verified.",
    RiskLevel.HIGH_RISK: "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
}

# Regex threat patterns with semantic descriptions, weights, and rule IDs
TEXT_THREAT_PATTERNS: List[Tuple[re.Pattern, str, float, str]] = [
    (
        re.compile(r"\baccount\s+(?:is\s+|will\s+be\s+|has\s+been\s+)?(?:suspended|blocked|frozen|deactivated|locked|closed)\b", re.IGNORECASE),
        "account suspension/blocking threat",
        0.35,
        "TXT_ACCOUNT_SUSPENSION",
    ),
    (
        re.compile(r"\b(?:verify|verification)\s+(?:immediately|now|here|identity|account|details)\b", re.IGNORECASE),
        "urgent verification demand",
        0.30,
        "TXT_URGENT_VERIFICATION",
    ),
    (
        re.compile(r"\b(?:update\s+kyc|kyc\s*(?:update|expired|mandatory|pending|deactivat\w*|expire\w*))\b", re.IGNORECASE),
        "KYC expiration or update lure",
        0.35,
        "TXT_KYC_LURE",
    ),
    (
        re.compile(r"\bpan\s+(?:card\s+)?(?:deactivat\w*|block\w*|link\w*|update\w*)\b", re.IGNORECASE),
        "PAN deactivation threat",
        0.35,
        "TXT_PAN_THREAT",
    ),
    (
        re.compile(r"\b(?:electricity|power)\s*(?:bill|supply)?\s*(?:is\s+|will\s+be\s+|has\s+been\s+)?(?:unpaid|disconnect\w*|cut)\b", re.IGNORECASE),
        "utility disconnection coercion",
        0.40,
        "TXT_UTILITY_DISCONNECT",
    ),
    (
        re.compile(r"\b(?:lottery|winner|won\s+(?:a\s+)?cashback|prize|reward\s+points?|lucky\s*draw)\b", re.IGNORECASE),
        "lottery or reward bait",
        0.35,
        "TXT_FINANCIAL_LURE",
    ),
    (
        re.compile(r"\b(?:enter|share|send|provide|give)\s+(?:me\s+|us\s+)?(?:your\s+|the\s+)?(?:otp|pin|password|cvv)\b", re.IGNORECASE),
        "credential or OTP solicitation",
        0.45,
        "TXT_CREDENTIAL_SOLICITATION",
    ),
    (
        re.compile(r"\b(?:urgent|immediately|within\s*24\s*hours?|action\s*required)\b", re.IGNORECASE),
        "coercive urgency pressure",
        0.20,
        "TXT_COERCIVE_URGENCY",
    ),
]


def score_to_risk_level(score: float) -> RiskLevel:
    """Map continuous score [0.0, 1.0] to discrete LinkSentry RiskLevel."""
    if score >= 0.80:
        return RiskLevel.HIGH_RISK
    elif score >= 0.60:
        return RiskLevel.SUSPICIOUS
    elif score >= 0.30:
        return RiskLevel.VERIFY_INDEPENDENTLY
    return RiskLevel.LOW


def score_to_action(level: RiskLevel) -> str:
    """Return PRD recommended action advisory."""
    return RECOMMENDED_ACTIONS.get(level, RECOMMENDED_ACTIONS[RiskLevel.LOW])


class TextAnalyzer:
    """Service for evaluating textual communication risks."""

    def __init__(self, text_model: Optional[BaseModel] = None) -> None:
        self.text_model = text_model or TextMLModel()

    def analyze(self, text: str, request_id: Optional[str] = None) -> TextAnalysisResponse:
        if not text or not text.strip():
            return TextAnalysisResponse(
                request_id=request_id,
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                category="benign",
                confidence=0.95,
                reasons=["No text provided."],
                indicators=[],
                model_status="active" if self.text_model.is_available else "unavailable",
                rules_triggered=[],
                extracted_urls=[],
                recommended_action=RECOMMENDED_ACTIONS[RiskLevel.LOW],
            )

        extracted_urls = extract_urls(text)
        reasons: List[str] = []
        indicators: List[str] = []
        rules_triggered: List[str] = []
        heuristic_score = 0.0

        # Evaluate semantic threat patterns
        for pattern, desc, weight, rule_id in TEXT_THREAT_PATTERNS:
            if pattern.search(text):
                reasons.append(f"Identified {desc}.")
                indicators.append(rule_id.lower())
                rules_triggered.append(rule_id)
                heuristic_score += weight

        # Heuristic 2: Excessive uppercase (urgency manipulation)
        letters = [c for c in text if c.isalpha()]
        if len(letters) >= 15:
            upper_ratio = sum(c.isupper() for c in letters) / len(letters)
            if upper_ratio > 0.45:
                heuristic_score += 0.20
                reasons.append("Excessive uppercase lettering indicates urgency manipulation.")
                indicators.append("excessive_uppercase")
                rules_triggered.append("TXT_URGENCY_CAPS")

        # Heuristic 3: Excessive punctuation (!!!, ???)
        if re.search(r"[!?]{2,}", text):
            heuristic_score += 0.15
            reasons.append("Aggressive punctuation marks detected.")
            indicators.append("aggressive_punctuation")
            rules_triggered.append("TXT_AGGRESSIVE_PUNCTUATION")

        heuristic_score = min(1.0, heuristic_score)

        # ML Model Inference (if real artifact is provided)
        ml_score, is_model_available = self.text_model.predict(text)

        if is_model_available and ml_score is not None:
            final_score = round(0.70 * ml_score + 0.30 * heuristic_score, 4)
            reasons.append(f"ML Classifier score: {ml_score:.2f}")
            confidence = 0.85
            model_status = "active"
        else:
            final_score = round(heuristic_score, 4)
            confidence = 0.85 if indicators else 0.95
            model_status = "unavailable"

        risk_level = score_to_risk_level(final_score)
        action = score_to_action(risk_level)

        # Category determination
        lower_text = text.lower()
        if any(k in lower_text for k in ("lottery", "winner", "cashback", "prize", "lucky draw")):
            category = "financial_lure"
        elif any(k in lower_text for k in ("kyc", "pan", "otp", "pin", "netbanking", "password")):
            category = "credential_harvesting"
        elif any(k in lower_text for k in ("suspended", "blocked", "electricity", "disconnect")):
            category = "urgency_coercion"
        elif final_score >= 0.40:
            category = "scam"
        else:
            category = "benign"

        return TextAnalysisResponse(
            request_id=request_id,
            risk_score=final_score,
            risk_level=risk_level,
            category=category,
            confidence=confidence,
            reasons=reasons,
            indicators=indicators,
            model_status=model_status,
            rules_triggered=rules_triggered,
            extracted_urls=extracted_urls,
            recommended_action=action,
        )
