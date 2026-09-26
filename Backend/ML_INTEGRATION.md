# LinkSentry Backend — ML Integration Guide

This guide details how Machine Learning (ML) engineers can train, export, and integrate model artifacts into the LinkSentry backend architecture.

---

## 1. Overview & Architecture Design

The backend is built around a pluggable **Adapter Architecture** using Python abstract base classes (`app/ml/base_model.py`).

The application **never crashes or fails** when trained model files are absent. In the initial development phase or when artifacts are missing:
- Model status is reported as `"unavailable"`.
- Inference calls safely return `(None, False)`.
- The system gracefully degrades to deterministic rule heuristics and lexical feature parsing.

---

## 2. Expected Model Artifacts & File Paths

To integrate trained models, export serialized `.joblib` artifacts into the `models/` directory or configure explicit file paths in `.env`:

```
models/
├── text/
│   ├── text_vectorizer.joblib     # Scikit-learn TfidfVectorizer
│   └── text_classifier.joblib     # Logistic Regression classifier
└── url/
    └── url_classifier.joblib      # Random Forest / Gradient Boosting classifier
```

### Environment Variable Configuration (`.env`)

```ini
# Absolute or relative paths to trained joblib artifacts
TEXT_VECTORIZER_PATH=models/text/text_vectorizer.joblib
TEXT_MODEL_PATH=models/text/text_classifier.joblib
URL_MODEL_PATH=models/url/url_classifier.joblib
```

---

## 3. Abstract Model Adapter Interface

All ML model adapters inherit from `BaseModel` (`app/ml/base_model.py`):

```python
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

class BaseModel(ABC):
    """Abstract base class for LinkSentry ML model adapters."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return semantic version of the model adapter."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if model artifacts are loaded and ready for inference."""
        pass

    @abstractmethod
    def predict(self, input_data: Any) -> Tuple[Optional[float], bool]:
        """
        Execute prediction inference.
        Returns: Tuple[risk_score_probability (0.0 to 1.0), is_successful_boolean]
        """
        pass
```

---

## 4. Text Model Integration Specifications

### 4.1 Required Artifacts
1. **`text_vectorizer.joblib`**: A fitted `sklearn.feature_extraction.text.TfidfVectorizer`.
2. **`text_classifier.joblib`**: A trained binary classifier (e.g. `sklearn.linear_model.LogisticRegression` or `CalibratedClassifierCV`) supporting `predict_proba()`.

### 4.2 Feature Expectations & Input Format
- **Input Data:** Raw preprocessed message text string (`str`).
- **Transformation:** Vectorizer transforms string to sparse 2D TF-IDF feature matrix:
  ```python
  X_tfidf = vectorizer.transform([text])
  ```
- **Prediction:** Classifier computes binary probability $P(\text{scam} = 1)$:
  ```python
  probabilities = classifier.predict_proba(X_tfidf)[0]
  scam_probability = float(probabilities[1])  # Class index 1 = Malicious/Scam
  ```

### 4.3 Adapter Target (`app/ml/text_model.py`)
The `TextMLModel` adapter automatically attempts to load artifacts from `TEXT_VECTORIZER_PATH` and `TEXT_MODEL_PATH`. When successfully loaded:
- `is_available` returns `True`.
- `model_status` reports `"active"`.
- `predict(text)` returns `(scam_probability, True)`.

---

## 5. URL Model Integration Specifications

### 5.1 Required Artifact
1. **`url_classifier.joblib`**: A trained binary tabular classifier (e.g. `sklearn.ensemble.RandomForestClassifier` or `HistGradientBoostingClassifier`) supporting `predict_proba()`.

### 5.2 Feature Expectations & Input Format
The URL analyzer extracts a structured dictionary of 35+ lexical and structural features via `extract_lexical_features(raw_url)` (`app/utils/url_utils.py`).

The URL model expects a numeric feature vector or `pandas.DataFrame` row containing keys such as:

```python
{
    "url_length": int,
    "hostname_length": int,
    "registered_domain_length": int,
    "path_length": int,
    "query_length": int,
    "fragment_length": int,
    "dot_count": int,
    "hyphen_count": int,
    "underscore_count": int,
    "slash_count": int,
    "at_count": int,
    "question_count": int,
    "equal_count": int,
    "ampersand_count": int,
    "percent_count": int,
    "digit_count": int,
    "subdomain_count": int,
    "path_depth": int,
    "is_https": int,             # 1 if https, 0 otherwise
    "is_ip_host": int,           # 1 if IP host, 0 otherwise
    "is_ipv4": int,
    "is_ipv6": int,
    "is_private_or_loopback_ip": int,
    "has_at_deception": int,
    "is_punycode": int,
    "is_idn": int,
    "is_shortener": int,
    "has_suspicious_tld": int,
    "hostname_entropy": float,
    "url_entropy": float,
    "query_param_count": int,
    "brand_domain_mismatch": int
}
```

### 5.3 Adapter Target (`app/ml/url_model.py`)
The `UrlMLModel` adapter automatically attempts to load `URL_MODEL_PATH`. When successfully loaded:
- `is_available` returns `True`.
- `model_status` reports `"active"`.
- `predict(extracted_features)` returns `(malicious_probability, True)`.

---

## 6. Verification & Adapter Testing

To test custom trained model artifacts against the backend adapter suite:

1. Place joblib files in `models/text/` and `models/url/`.
2. Update `.env` paths:
   ```ini
   TEXT_VECTORIZER_PATH=models/text/text_vectorizer.joblib
   TEXT_MODEL_PATH=models/text/text_classifier.joblib
   URL_MODEL_PATH=models/url/url_classifier.joblib
   ```
3. Run the automated ML adapter test suite:
   ```bash
   d:\LinkSentry\Backend\.venv\Scripts\pytest tests/test_ml_adapters.py -v
   ```
4. Query `GET /api/model-info` to verify status reports `"active"`.
