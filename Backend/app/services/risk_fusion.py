import logging
from typing import List, Optional
import uuid

from app.core.config import get_settings
from app.schemas.analyze import (
    CombinedAnalysisResponse,
    RiskLevel,
    RulesEngineResult,
    TextAnalysisResponse,
    UrlAnalysisResponse,
)

logger = logging.getLogger(__name__)

# Standard recommended action advisories per LinkSentry PRD
RECOMMENDED_ACTIONS = {
    RiskLevel.LOW: "Continue normally, while remaining cautious.",
    RiskLevel.VERIFY_INDEPENDENTLY: "Verify the request using an official source before taking action.",
    RiskLevel.SUSPICIOUS: "Do not provide sensitive information or make a payment until independently verified.",
    RiskLevel.HIGH_RISK: "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
}

# Critical rule IDs that trigger high-risk or suspicious escalation
CRITICAL_RULE_IDS = {
    "RULE_OTP_REQUEST",
    "RULE_REMOTE_ACCESS",
    "RULE_IP_HOST",
    "RULE_BRAND_DOMAIN_MISMATCH",
    "TXT_UPI_COLLECT_SCAM",
    "TXT_CREDENTIAL_SOLICITATION",
    "TXT_ACCOUNT_SUSPENSION",
    "URL_AT_DECEPTION",
    "URL_IP_HOST",
}


class RiskFusionService:
    """
    Service for multi-modal risk fusion across Text, URL, and Heuristic Rules.
    
    Adheres strictly to:
    - Configurable weights (Defaults: Text 0.45, URL 0.35, Rules 0.20)
    - Missing input normalization (never treat missing input as safe)
    - Multi-URL independent evaluation
    - Explainable rule integration
    - Standardized non-definitive security advisories
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.text_weight = getattr(self.settings, "TEXT_WEIGHT", 0.45)
        self.url_weight = getattr(self.settings, "URL_WEIGHT", 0.35)
        self.rule_weight = getattr(self.settings, "RULE_WEIGHT", 0.20)
        self.thresholds = getattr(
            self.settings,
            "RISK_THRESHOLDS",
            {"low": 0.29, "verify_independently": 0.59, "suspicious": 0.79, "high_risk": 1.0},
        )

    def _available_weight_sum(
        self,
        text: Optional[TextAnalysisResponse],
        urls: List[UrlAnalysisResponse],
        rules: Optional[RulesEngineResult],
    ) -> float:
        """Calculate the sum of weights for available signals only."""
        total = 0.0
        if text is not None:
            total += self.text_weight
        if urls and len(urls) > 0:
            total += self.url_weight
        if rules is not None and len(rules.matched_rules) > 0:
            total += self.rule_weight
        return total if total > 0 else 1.0

    def _map_score_to_level(self, score: float) -> RiskLevel:
        """Map normalized risk score to discrete LinkSentry RiskLevel."""
        if score <= self.thresholds.get("low", 0.29):
            return RiskLevel.LOW
        elif score <= self.thresholds.get("verify_independently", 0.59):
            return RiskLevel.VERIFY_INDEPENDENTLY
        elif score <= self.thresholds.get("suspicious", 0.79):
            return RiskLevel.SUSPICIOUS
        return RiskLevel.HIGH_RISK

    def _get_action_for_level(self, level: RiskLevel) -> str:
        """Return standardized user advisory based on RiskLevel."""
        return RECOMMENDED_ACTIONS.get(level, RECOMMENDED_ACTIONS[RiskLevel.LOW])

    def fuse(
        self,
        text_result: Optional[TextAnalysisResponse] = None,
        url_results: Optional[List[UrlAnalysisResponse]] = None,
        rules_result: Optional[RulesEngineResult] = None,
        request_id: Optional[str] = None,
    ) -> CombinedAnalysisResponse:
        """
        Fuse multi-modal risk signals into a comprehensive, explainable assessment.
        """
        urls = url_results or []

        # Calculate representative component scores
        text_score = text_result.risk_score if text_result is not None else 0.0
        # Use maximum URL risk score if multiple URLs are present
        url_score = max((u.risk_score for u in urls), default=0.0)
        rules_score = rules_result.score if rules_result is not None else 0.0

        # Weighted normalization across available signals
        weight_sum = self._available_weight_sum(text_result, urls, rules_result)
        weighted_total = (
            (text_score * self.text_weight if text_result is not None else 0.0)
            + (url_score * self.url_weight if urls else 0.0)
            + (rules_score * self.rule_weight if (rules_result and rules_result.matched_rules) else 0.0)
        )
        final_score = round(min(1.0, weighted_total / weight_sum), 4)

        # Map to discrete risk level
        level = self._map_score_to_level(final_score)

        # Aggregate triggered rule IDs
        triggered_rules: List[str] = []
        if rules_result:
            triggered_rules.extend(r.rule_id for r in rules_result.matched_rules)
        if text_result:
            triggered_rules.extend(text_result.rules_triggered)
        for u in urls:
            triggered_rules.extend(u.triggered_rules)
        # Deduplicate preserving order
        deduped_rules = list(dict.fromkeys(triggered_rules))

        # Critical escalation: Escalate if severe indicators match
        has_critical_rule = any(r in CRITICAL_RULE_IDS for r in deduped_rules)
        if has_critical_rule:
            if final_score >= 0.50:
                level = RiskLevel.HIGH_RISK
            elif level == RiskLevel.LOW or level == RiskLevel.VERIFY_INDEPENDENTLY:
                level = RiskLevel.SUSPICIOUS

        # Construct concise, non-definitive summary
        if level == RiskLevel.HIGH_RISK:
            summary = "High risk detected with critical indicators of scam or phishing patterns."
        elif level == RiskLevel.SUSPICIOUS:
            summary = "Suspicious signals detected in message or link structure."
        elif level == RiskLevel.VERIFY_INDEPENDENTLY:
            summary = "Potential risk indicators present; independent verification recommended."
        else:
            summary = "No immediate high-risk indicators detected."

        return CombinedAnalysisResponse(
            request_id=request_id or str(uuid.uuid4()),
            final_risk_score=final_score,
            final_risk_level=level,
            text_analysis=text_result,
            url_analysis=urls,
            rules_triggered=deduped_rules,
            recommended_action=self._get_action_for_level(level),
            summary=summary,
        )


# Singleton instance and backward compatibility helper
risk_fusion_service = RiskFusionService()


def fuse_risk(
    text_result: Optional[TextAnalysisResponse] = None,
    url_result: Optional[List[UrlAnalysisResponse] | UrlAnalysisResponse] = None,
    rules_result: Optional[RulesEngineResult] = None,
    request_id: Optional[str] = None,
    extracted_urls: Optional[List[str]] = None,
) -> CombinedAnalysisResponse:
    """Backward compatibility wrapper."""
    url_results: List[UrlAnalysisResponse] = []
    if isinstance(url_result, list):
        url_results = url_result
    elif url_result is not None:
        url_results = [url_result]

    return risk_fusion_service.fuse(
        text_result=text_result,
        url_results=url_results,
        rules_result=rules_result,
        request_id=request_id,
    )
