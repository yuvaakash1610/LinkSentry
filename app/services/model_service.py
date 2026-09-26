from typing import List, Optional
from app.core.config import get_settings
from app.ml.base_model import BaseModel
from app.ml.text_model import TextMLModel
from app.ml.url_model import UrlMLModel
from app.schemas.analyze import (
    CombinedAnalysisResponse,
    ModelComponentInfo,
    ModelInfoResponse,
    TextAnalysisResponse,
    UrlAnalysisResponse,
)
from app.services.risk_fusion import RiskFusionService, fuse_risk
from app.services.rules_engine import evaluate_rules
from app.services.text_analyzer import TextAnalyzer, score_to_risk_level, score_to_action
from app.services.url_analyzer import UrlAnalyzer
from app.services.url_extractor import extract_urls


class ModelService:
    """
    Central orchestration service integrating Text Analyzer, URL Analyzer,
    URL Extractor, Rules Engine, Risk Fusion, and ML Adapters.
    """

    def __init__(
        self,
        text_model: Optional[BaseModel] = None,
        url_model: Optional[BaseModel] = None,
    ) -> None:
        settings = get_settings()
        self.text_model = text_model or TextMLModel(
            model_path=settings.TEXT_MODEL_PATH,
            vectorizer_path=settings.TEXT_VECTORIZER_PATH,
        )
        self.url_model = url_model or UrlMLModel(
            model_path=settings.URL_MODEL_PATH,
        )
        self.text_analyzer = TextAnalyzer(self.text_model)
        self.url_analyzer = UrlAnalyzer(self.url_model)
        self.risk_fusion = RiskFusionService()

    def analyze_text_content(
        self, text: str, request_id: Optional[str] = None
    ) -> TextAnalysisResponse:
        """
        Execute Text Analysis Pipeline:
        request -> validation -> preprocessing -> URL extraction -> text analysis -> rules -> final result
        """
        # Step 1: Text analysis & URL extraction
        text_result = self.text_analyzer.analyze(text, request_id=request_id)

        # Step 2: Evaluate rules on text and first extracted URL (if present)
        primary_url = text_result.extracted_urls[0] if text_result.extracted_urls else None
        first_url_features = None
        if primary_url:
            first_url_res = self.url_analyzer.analyze(primary_url)
            first_url_features = first_url_res.extracted_features

        rules_result = evaluate_rules(
            text=text,
            url=primary_url,
            url_features=first_url_features,
        )

        # Step 3: Merge triggered rule IDs
        rule_ids = [r.rule_id for r in rules_result.matched_rules]
        all_rules = list(dict.fromkeys(text_result.rules_triggered + rule_ids))
        text_result.rules_triggered = all_rules

        # Step 4: If rules elevated risk score, adjust final text score
        if rules_result.score > text_result.risk_score:
            fused_score = round(0.70 * text_result.risk_score + 0.30 * rules_result.score, 4)
            text_result.risk_score = max(text_result.risk_score, fused_score)
            text_result.risk_level = score_to_risk_level(text_result.risk_score)
            text_result.recommended_action = score_to_action(text_result.risk_level)

        return text_result

    def analyze_url_content(
        self, url: str, request_id: Optional[str] = None
    ) -> UrlAnalysisResponse:
        """
        Execute URL Analysis Pipeline:
        request -> validation -> URL parsing -> feature extraction -> ML if available -> rules -> final result
        """
        # Step 1: Feature extraction, heuristics, ML inference
        url_result = self.url_analyzer.analyze(url)

        # Step 2: Rules engine evaluation
        rules_result = evaluate_rules(
            text=None,
            url=url,
            url_features=url_result.extracted_features,
        )

        # Step 3: Merge triggered rule IDs
        rule_ids = [r.rule_id for r in rules_result.matched_rules]
        all_rules = list(dict.fromkeys(url_result.triggered_rules + rule_ids))
        url_result.triggered_rules = all_rules

        # Step 4: Elevate score if rules engine detected higher risk
        if rules_result.score > url_result.risk_score:
            fused_score = round(0.70 * url_result.risk_score + 0.30 * rules_result.score, 4)
            url_result.risk_score = max(url_result.risk_score, fused_score)
            url_result.risk_level = score_to_risk_level(url_result.risk_score)

        return url_result

    def analyze_combined_content(
        self,
        text: Optional[str] = None,
        urls: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> CombinedAnalysisResponse:
        """
        Execute Combined Multi-Modal Analysis Pipeline:
        request -> validation -> text preprocessing -> URL extraction -> text analysis
        -> URL analysis (per-URL) -> rules -> risk fusion -> explanation -> recommendation
        """
        # Step 1: Consolidate and deduplicate URLs from input list and text payload
        submitted_urls = urls or []
        extracted_from_text = extract_urls(text) if text else []
        # Preserve discovery order while deduplicating
        all_unique_urls = list(dict.fromkeys(submitted_urls + extracted_from_text))

        # Step 2: Text analysis if text is present
        text_result = self.text_analyzer.analyze(text, request_id=request_id) if text else None

        # Step 3: Per-URL analysis for each deduplicated URL
        url_results: List[UrlAnalysisResponse] = []
        for u in all_unique_urls:
            url_results.append(self.url_analyzer.analyze(u))

        # Step 4: Rules evaluation across text and primary URL features
        primary_url = all_unique_urls[0] if all_unique_urls else None
        first_url_features = url_results[0].extracted_features if url_results else None
        rules_result = evaluate_rules(
            text=text,
            url=primary_url,
            url_features=first_url_features,
        )

        # Step 5: Multi-modal Risk Fusion
        return self.risk_fusion.fuse(
            text_result=text_result,
            url_results=url_results,
            rules_result=rules_result,
            request_id=request_id,
        )

    def analyze_qr_content(
        self, content: str, request_id: Optional[str] = None
    ) -> CombinedAnalysisResponse:
        """
        Execute QR Analysis Pipeline for decoded QR payloads.
        """
        extracted = extract_urls(content)
        if extracted:
            # QR contains URL or payment link
            if content.strip() == extracted[0]:
                return self.analyze_combined_content(
                    text=None, urls=[extracted[0]], request_id=request_id
                )
            return self.analyze_combined_content(
                text=content, urls=[extracted[0]], request_id=request_id
            )
        else:
            return self.analyze_combined_content(
                text=content, urls=[], request_id=request_id
            )

    def get_model_info(self) -> ModelInfoResponse:
        """Safe metadata about models without exposing internal filesystem paths."""
        return ModelInfoResponse(
            text_model=ModelComponentInfo(
                name="TF-IDF + Logistic Regression",
                version=self.text_model.model_version,
                status=self.text_model.model_status,
            ),
            url_model=ModelComponentInfo(
                name="Lexical Random Forest",
                version=self.url_model.model_version,
                status=self.url_model.model_status,
            ),
        )


# Module-level singleton instance
_model_service_instance: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Dependency provider for ModelService."""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    return _model_service_instance
