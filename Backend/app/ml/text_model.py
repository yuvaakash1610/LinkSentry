import os
from typing import Optional, Tuple
import joblib
from app.core.logging import get_logger
from .base_model import BaseModel

logger = get_logger(__name__)


class TextMLModel(BaseModel):
    """
    Inference interface for Text Phishing/Scam Classifier.
    
    Expected Architecture: TF-IDF Vectorizer + Logistic Regression Classifier.
    When model artifacts are present, predicts probability of maliciousness (0.0 to 1.0).
    When artifacts are not loaded, cleanly signals unavailability without faking inferences.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        vectorizer_path: Optional[str] = None,
    ) -> None:
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self._model = None
        self._vectorizer = None
        self._is_loaded = False
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load serialized TF-IDF vectorizer and Logistic Regression model if paths exist."""
        if not self.model_path or not self.vectorizer_path:
            logger.info("Text ML model paths not configured. Operating in heuristic/rule mode.")
            return

        if not os.path.exists(self.model_path) or not os.path.exists(self.vectorizer_path):
            logger.info(
                "Text ML model artifacts not found on disk. Operating in heuristic/rule mode."
            )
            return

        try:
            self._model = joblib.load(self.model_path)
            self._vectorizer = joblib.load(self.vectorizer_path)
            self._is_loaded = True
            logger.info("Successfully loaded Text ML model and vectorizer.")
        except Exception as exc:
            self._is_loaded = False
            logger.error("Failed to load Text ML model artifacts: %s", exc)

    @property
    def model_version(self) -> str:
        return "1.0.0"

    @property
    def model_status(self) -> str:
        return "active" if self.is_available else "unavailable"

    @property
    def is_available(self) -> bool:
        """Return True only if real serialized model artifacts are loaded in memory."""
        return self._is_loaded and self._model is not None and self._vectorizer is not None

    def predict(self, data: str) -> Tuple[Optional[float], bool]:
        """Conform to BaseModel predict interface."""
        return self.predict_risk(data)

    def predict_proba(self, data: str) -> Tuple[Optional[Tuple[float, float]], bool]:
        """Return (benign_prob, malicious_prob) tuple and availability flag."""
        risk, available = self.predict_risk(data)
        if not available or risk is None:
            return None, False
        return (round(1.0 - risk, 4), round(risk, 4)), True

    def predict_risk(self, text: str) -> Tuple[Optional[float], bool]:
        """
        Predict probability of text being a scam/phishing message.

        Returns:
            Tuple[Optional[float], bool]: (risk_probability_or_none, is_model_available)
            - If model is available: (probability 0.0-1.0, True)
            - If model is not available: (None, False)
        """
        if not self.is_available:
            return None, False

        try:
            vec = self._vectorizer.transform([text])
            # Assuming binary classifier where class 1 is malicious/scam
            probabilities = self._model.predict_proba(vec)[0]
            # Probability of scam class
            scam_prob = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
            return round(scam_prob, 4), True
        except Exception as exc:
            logger.error("Text ML prediction error: %s", exc)
            return None, False
