import os
from typing import Any, Dict, Optional, Tuple
import pytest
from app.ml.base_model import BaseModel
from app.ml.text_model import TextMLModel
from app.ml.url_model import UrlMLModel
from app.schemas.analyze import RiskLevel
from app.services.model_service import ModelService, get_model_service
from app.services.text_analyzer import TextAnalyzer
from app.services.url_analyzer import UrlAnalyzer


class MockTextModel(BaseModel):
    """Mock text model adapter for testing."""

    def __init__(self, score: float = 0.95, available: bool = True) -> None:
        self._score = score
        self._available = available

    @property
    def model_version(self) -> str:
        return "mock-text-v1"

    @property
    def model_status(self) -> str:
        return "active" if self._available else "unavailable"

    @property
    def is_available(self) -> bool:
        return self._available

    def predict(self, data: str) -> Tuple[Optional[float], bool]:
        if not self._available:
            return None, False
        return self._score, True

    def predict_proba(self, data: str) -> Tuple[Optional[Tuple[float, float]], bool]:
        if not self._available:
            return None, False
        return (round(1.0 - self._score, 4), round(self._score, 4)), True

    def predict_risk(self, text: str) -> Tuple[Optional[float], bool]:
        return self.predict(text)


class MockUrlModel(BaseModel):
    """Mock URL model adapter for testing."""

    def __init__(self, score: float = 0.90, available: bool = True) -> None:
        self._score = score
        self._available = available

    @property
    def model_version(self) -> str:
        return "mock-url-v1"

    @property
    def model_status(self) -> str:
        return "active" if self._available else "unavailable"

    @property
    def is_available(self) -> bool:
        return self._available

    def predict(self, data: Dict[str, Any]) -> Tuple[Optional[float], bool]:
        if not self._available:
            return None, False
        return self._score, True

    def predict_proba(self, data: Dict[str, Any]) -> Tuple[Optional[Tuple[float, float]], bool]:
        if not self._available:
            return None, False
        return (round(1.0 - self._score, 4), round(self._score, 4)), True

    def predict_risk(self, features: Dict[str, Any]) -> Tuple[Optional[float], bool]:
        return self.predict(features)


def test_text_ml_model_missing_artifacts():
    """TextMLModel must gracefully handle missing model files and signal unavailability."""
    model = TextMLModel(
        model_path="nonexistent_text_classifier.joblib",
        vectorizer_path="nonexistent_text_vectorizer.joblib",
    )
    assert model.is_available is False
    assert model.model_status == "unavailable"
    assert model.model_version == "1.0.0"

    score, available = model.predict("Urgent: Your account is suspended!")
    assert available is False
    assert score is None

    proba, available = model.predict_proba("Urgent: Your account is suspended!")
    assert available is False
    assert proba is None


def test_url_ml_model_missing_artifacts():
    """UrlMLModel must gracefully handle missing model files and signal unavailability."""
    model = UrlMLModel(model_path="nonexistent_url_classifier.joblib")
    assert model.is_available is False
    assert model.model_status == "unavailable"
    assert model.model_version == "1.0.0"

    score, available = model.predict({"url_length": 50, "has_at_deception": False})
    assert available is False
    assert score is None

    proba, available = model.predict_proba({"url_length": 50, "has_at_deception": False})
    assert available is False
    assert proba is None


def test_text_ml_model_corrupt_artifact(tmp_path):
    """TextMLModel must safely handle invalid/corrupt artifact files without crashing."""
    corrupt_model = tmp_path / "corrupt_model.joblib"
    corrupt_vectorizer = tmp_path / "corrupt_vectorizer.joblib"
    corrupt_model.write_text("invalid binary data", encoding="utf-8")
    corrupt_vectorizer.write_text("invalid binary data", encoding="utf-8")

    model = TextMLModel(
        model_path=str(corrupt_model),
        vectorizer_path=str(corrupt_vectorizer),
    )
    assert model.is_available is False
    assert model.model_status == "unavailable"

    score, available = model.predict("Hello world")
    assert available is False
    assert score is None


def test_url_ml_model_corrupt_artifact(tmp_path):
    """UrlMLModel must safely handle invalid/corrupt artifact files without crashing."""
    corrupt_model = tmp_path / "corrupt_model.joblib"
    corrupt_model.write_text("not a valid pickle/joblib payload", encoding="utf-8")

    model = UrlMLModel(model_path=str(corrupt_model))
    assert model.is_available is False
    assert model.model_status == "unavailable"

    score, available = model.predict({})
    assert available is False
    assert score is None


def test_text_analyzer_with_mock_adapter():
    """TextAnalyzer correctly fuses mock ML model inferences with heuristic signals."""
    mock_model = MockTextModel(score=0.90, available=True)
    analyzer = TextAnalyzer(text_model=mock_model)

    response = analyzer.analyze("Your account is suspended. Verify immediately.")
    assert response.model_status == "active"
    assert response.risk_score > 0.70
    assert response.risk_level == RiskLevel.HIGH_RISK
    assert any("ML Classifier score" in reason for reason in response.reasons)


def test_url_analyzer_with_mock_adapter():
    """UrlAnalyzer correctly fuses mock ML model inferences with heuristic signals."""
    mock_model = MockUrlModel(score=0.88, available=True)
    analyzer = UrlAnalyzer(url_model=mock_model)

    response = analyzer.analyze("https://secure-login.suspicious-domain.xyz/verify")
    assert response.model_status == "active"
    assert response.model_prediction == 0.88
    assert response.risk_score > 0.60


def test_model_service_adapter_injection():
    """ModelService integrates injected adapters into get_model_info and analysis pipelines."""
    mock_text = MockTextModel(score=0.85, available=True)
    mock_url = MockUrlModel(score=0.80, available=True)

    service = ModelService(text_model=mock_text, url_model=mock_url)
    info = service.get_model_info()

    assert info.text_model.version == "mock-text-v1"
    assert info.text_model.status == "active"
    assert info.url_model.version == "mock-url-v1"
    assert info.url_model.status == "active"

    combined = service.analyze_combined_content(
        text="Update KYC immediately",
        urls=["https://update-kyc.top/login"],
    )
    assert combined.final_risk_score > 0.50


def test_model_service_singleton_caching():
    """get_model_service should return the cached singleton instance."""
    instance1 = get_model_service()
    instance2 = get_model_service()
    assert instance1 is instance2
