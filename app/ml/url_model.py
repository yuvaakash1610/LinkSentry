import os
from typing import Any, Dict, Optional, Tuple
import joblib
import pandas as pd
from app.core.logging import get_logger
from .base_model import BaseModel

logger = get_logger(__name__)


class UrlMLModel(BaseModel):
    """
    Inference interface for Lexical/Structural URL Random Forest Classifier.
    
    Expected Architecture: Tabular Random Forest Classifier trained on lexical URL features.
    When model artifacts are present, predicts probability of maliciousness (0.0 to 1.0).
    When artifacts are not loaded, cleanly signals unavailability without fabricating predictions.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path
        self._model = None
        self._is_loaded = False
        self._load_artifact()

    def _load_artifact(self) -> None:
        """Load serialized Random Forest model if path exists."""
        if not self.model_path:
            logger.info("URL ML model path not configured. Operating in lexical/rule mode.")
            return

        if not os.path.exists(self.model_path):
            logger.info("URL ML model artifact not found on disk. Operating in lexical/rule mode.")
            return

        try:
            self._model = joblib.load(self.model_path)
            self._is_loaded = True
            logger.info("Successfully loaded URL ML Random Forest model.")
        except Exception as exc:
            self._is_loaded = False
            logger.error("Failed to load URL ML model artifact: %s", exc)

    @property
    def model_version(self) -> str:
        return "1.0.0"

    @property
    def model_status(self) -> str:
        return "active" if self.is_available else "unavailable"

    @property
    def is_available(self) -> bool:
        """Return True only if real serialized model artifact is loaded in memory."""
        return self._is_loaded and self._model is not None

    def predict(self, data: Dict[str, Any]) -> Tuple[Optional[float], bool]:
        """Conform to BaseModel predict interface."""
        return self.predict_risk(data)

    def predict_proba(self, data: Dict[str, Any]) -> Tuple[Optional[Tuple[float, float]], bool]:
        """Return (benign_prob, malicious_prob) tuple and availability flag."""
        risk, available = self.predict_risk(data)
        if not available or risk is None:
            return None, False
        return (round(1.0 - risk, 4), round(risk, 4)), True

    def predict_risk(self, features: Dict[str, Any]) -> Tuple[Optional[float], bool]:
        """
        Predict probability of URL being malicious based on lexical/structural features.

        Returns:
            Tuple[Optional[float], bool]: (risk_probability_or_none, is_model_available)
            - If model is available: (probability 0.0-1.0, True)
            - If model is not available: (None, False)
        """
        if not self.is_available:
            return None, False

        try:
            # Filter tabular numerical/boolean feature columns suitable for Random Forest
            tabular_features = {
                k: v for k, v in features.items()
                if isinstance(v, (int, float, bool))
            }
            df = pd.DataFrame([tabular_features])
            probabilities = self._model.predict_proba(df)[0]
            malicious_prob = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])
            return round(malicious_prob, 4), True
        except Exception as exc:
            logger.error("URL ML prediction error: %s", exc)
            return None, False
