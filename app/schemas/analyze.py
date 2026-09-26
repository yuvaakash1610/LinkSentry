from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator
import validators

SUPPORTED_SCHEMES = {"http", "https", "ftp", "upi"}


class RiskLevel(str, Enum):
    LOW = "low"
    VERIFY_INDEPENDENTLY = "verify_independently"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"


# Backwards compatibility alias
RiskTier = RiskLevel


class ActionRecommendation(str, Enum):
    ALLOW = "allow"
    VERIFY_INDEPENDENTLY = "verify_independently"
    CAUTION = "caution"
    BLOCK = "block"


# --- Request Schemas ---

class TextAnalysisRequest(BaseModel):
    """Payload for analyzing suspicious message text or notification snippet."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The raw message content received on device",
        examples=["URGENT: Your account is locked. Verify at http://bank-verify.example"],
    )
    source: Optional[str] = Field(
        "manual_paste",
        description="Origin source of text (e.g., manual_paste, notification, sms)",
    )
    language_hint: Optional[str] = Field(
        "en",
        description="Expected language code (e.g., en, es, hi)",
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty_or_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or whitespace-only.")
        return v.strip()


class UrlAnalysisRequest(BaseModel):
    """Payload for analyzing an isolated suspicious URL string."""
    url: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The URL string to evaluate without remote fetching",
        examples=["https://example.com"],
    )
    source: Optional[str] = Field(
        "manual_paste",
        description="Origin source of URL (e.g., manual_paste, browser_intercept)",
    )

    @field_validator("url")
    @classmethod
    def validate_url_syntax_and_scheme(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("URL cannot be empty or whitespace-only.")
        cleaned = v.strip()

        parsed = urlparse(cleaned)
        scheme = parsed.scheme.lower()
        if not scheme:
            # If scheme missing, prepend https:// for validation check
            test_url = "https://" + cleaned
            parsed = urlparse(test_url)
            scheme = "https"
            cleaned = test_url

        if scheme not in SUPPORTED_SCHEMES:
            raise ValueError(
                f"Unsupported URL scheme '{scheme}'. Supported schemes: {', '.join(sorted(SUPPORTED_SCHEMES))}"
            )

        if not parsed.netloc and scheme != "upi":
            raise ValueError("Invalid URL: Missing hostname or network location.")

        # Static syntax validation (never fetch!)
        if scheme in ("http", "https", "ftp") and not validators.url(cleaned):
            raise ValueError("Invalid URL syntax.")

        return cleaned


class CombinedAnalysisRequest(BaseModel):
    """Payload for evaluating message context alongside URL evidence."""
    text: Optional[str] = Field(
        None,
        max_length=10000,
        description="Optional accompanying message text",
    )
    urls: List[str] = Field(
        default_factory=list,
        description="List of URL strings to evaluate alongside text",
    )
    url: Optional[str] = Field(
        None,
        max_length=4096,
        description="Single URL alternative for backwards compatibility",
    )
    source: Optional[str] = Field(
        "manual_paste",
        description="Origin source of submission",
    )
    language_hint: Optional[str] = Field(
        "en",
        description="Expected language code",
    )

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    @field_validator("urls")
    @classmethod
    def validate_urls_list(cls, v: List[str]) -> List[str]:
        cleaned_urls = []
        for u in v:
            if not u or not u.strip():
                continue
            cleaned = u.strip()
            parsed = urlparse(cleaned)
            scheme = parsed.scheme.lower() or "https"
            if scheme not in SUPPORTED_SCHEMES:
                raise ValueError(f"Unsupported URL scheme in urls: '{scheme}'")
            cleaned_urls.append(cleaned)
        return cleaned_urls

    @model_validator(mode="after")
    def verify_at_least_one_field(self) -> "CombinedAnalysisRequest":
        has_text = bool(self.text and self.text.strip())
        has_urls = bool(self.urls and len(self.urls) > 0)
        has_single_url = bool(self.url and self.url.strip())

        if not (has_text or has_urls or has_single_url):
            raise ValueError("At least text OR URL must be provided.")

        # Consolidate single url into urls list if present
        if has_single_url and self.url.strip() not in self.urls:
            self.urls.append(self.url.strip())

        return self


class QrAnalysisRequest(BaseModel):
    """Payload for evaluating raw content extracted from a QR code."""
    content: Optional[str] = Field(
        None,
        max_length=10000,
        description="Raw string content extracted from scanned QR code",
        examples=["https://example.com"],
    )
    payload: Optional[str] = Field(
        None,
        max_length=10000,
        description="Alias for content for backwards compatibility",
    )
    source: Optional[str] = Field(
        "qr",
        description="Source of QR content",
    )

    @model_validator(mode="after")
    def validate_content_presence(self) -> "QrAnalysisRequest":
        raw = self.content or self.payload
        if not raw or not raw.strip():
            raise ValueError("QR content cannot be empty or whitespace-only.")
        self.content = raw.strip()
        self.payload = raw.strip()
        return self


# --- Intermediate & Sub-Analysis Response Schemas ---

class TextAnalysisResponse(BaseModel):
    """Detailed response for text analysis."""
    request_id: Optional[str] = Field(None, description="Request correlation identifier")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score from 0.0 to 1.0")
    risk_level: RiskLevel = Field(..., description="Qualitative risk tier: low, verify_independently, suspicious, high_risk")
    category: str = Field(..., description="Classification category (e.g., scam, phishing, benign, financial_lure)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model/heuristic prediction confidence")
    reasons: List[str] = Field(default_factory=list, description="Explanatory reasons for assigned risk")
    indicators: List[str] = Field(default_factory=list, description="Primary threat indicators detected")
    model_status: str = Field("unavailable", description="Status of text ML model (active or unavailable)")
    rules_triggered: List[str] = Field(default_factory=list, description="List of rule IDs triggered")
    extracted_urls: List[str] = Field(default_factory=list, description="List of URLs discovered in the text")
    recommended_action: Optional[str] = Field(None, description="Recommended client action")


# Alias for internal service compatibility
TextAnalysisResult = TextAnalysisResponse


class UrlAnalysisResponse(BaseModel):
    """Detailed response for URL analysis."""
    url: str = Field(..., description="Evaluated URL")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score from 0.0 to 1.0")
    risk_level: RiskLevel = Field(..., description="Qualitative risk tier: low, verify_independently, suspicious, high_risk")
    hostname: str = Field(..., description="Extracted network host or domain")
    registered_domain: str = Field(..., description="Registered pay-level domain")
    indicators: List[str] = Field(default_factory=list, description="Detected lexical indicators")
    extracted_features: Dict[str, Any] = Field(default_factory=dict, description="Lexical and structural features")
    model_prediction: Optional[float] = Field(None, description="Prediction probability from ML model, if available")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    model_status: str = Field("unavailable", description="Status of URL ML model (active or unavailable)")
    triggered_rules: List[str] = Field(default_factory=list, description="List of rule IDs triggered")
    claimed_brand: Optional[str] = Field(None, description="Brand name detected in authority or path")
    brand_domain_mismatch: bool = Field(False, description="Flag indicating brand mention without corresponding registered domain")
    is_ip_host: bool = Field(False, description="Flag indicating raw IP address host")
    is_shortener: bool = Field(False, description="Flag indicating URL shortener domain")


# Alias for internal service compatibility
UrlAnalysisResult = UrlAnalysisResponse


class RuleMatch(BaseModel):
    rule_id: str
    description: str
    severity: str
    weight: float
    # Explainable output fields
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized rule score (0.0-1.0)")
    reason: str = Field(..., description="Human‑readable reason why the rule was triggered")
    evidence_type: str = Field(..., description="Type of evidence that caused the trigger (e.g., 'text', 'url')")


class RulesEngineResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Accumulated heuristic rule score")
    matched_rules: List[RuleMatch] = Field(default_factory=list)


# --- Combined & Unified High-Level Response Schemas ---

class CombinedAnalysisResponse(BaseModel):
    """
    Standard comprehensive response model for LinkSentry multi-modal analysis.
    Supports combined text + URL evaluation, QR scans, and unified risk fusion.
    """
    request_id: str = Field(..., description="Correlation request ID")
    final_risk_score: float = Field(..., ge=0.0, le=1.0, description="Consolidated risk score (0.0 to 1.0)")
    final_risk_level: RiskLevel = Field(..., description="Consolidated risk level: low, verify_independently, suspicious, high_risk")
    text_analysis: Optional[TextAnalysisResponse] = Field(None, description="Text sub-analysis results")
    url_analysis: List[UrlAnalysisResponse] = Field(default_factory=list, description="URL sub-analysis results")
    rules_triggered: List[str] = Field(default_factory=list, description="All rule IDs triggered across analysis")
    recommended_action: str = Field(..., description="Actionable client advice (allow, verify_independently, caution, block)")
    summary: Optional[str] = Field(None, description="Human-friendly summary for the user")


# Alias for compatibility with previous naming
UnifiedAnalysisResponse = CombinedAnalysisResponse


# --- Model Info Schemas ---

class ModelComponentInfo(BaseModel):
    name: str = Field(..., description="Model architecture/framework name")
    version: str = Field(..., description="Model semantic version")
    status: str = Field(..., description="Current status: available, unavailable, or active")


class ModelInfoResponse(BaseModel):
    """Safe model metadata without exposing filesystem paths or credentials."""
    text_model: ModelComponentInfo
    url_model: ModelComponentInfo
