from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple


class BaseModel(ABC):
    """Abstract interface for all ML model adapters.

    Implementations must provide methods for prediction, probability, version
    information and availability status without exposing filesystem details.
    """

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return a human-readable version identifier for the model."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_status(self) -> str:
        """Return 'active' or 'unavailable' depending on artifact loading."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if the underlying artifact is correctly loaded and ready for inference."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, data: Any) -> Tuple[Optional[float], bool]:
        """Return a risk score (0-1) and availability flag.

        data is model-specific (text string or feature dict). If the model is not
        available the method must return (None, False).
        """
        raise NotImplementedError

    @abstractmethod
    def predict_proba(self, data: Any) -> Tuple[Optional[Tuple[float, float]], bool]:
        """Return a (benign_prob, malicious_prob) probability tuple and availability flag."""
        raise NotImplementedError
