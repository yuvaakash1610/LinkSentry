# LinkSentry Backend

> **"Think before you tap"**

LinkSentry is a high-performance, privacy-first cybersecurity backend designed to protect mobile users from SMS scams, fraudulent notifications, phishing links, and malicious QR code payloads.

The backend serves as the core intelligence engine for the LinkSentry Android application. It processes untrusted text messages, standalone URLs, combined textual/link contexts, and decoded QR string payloads to compute transparent, explainable risk scores and actionable security advice.

---

## 1. Key Features & Guarantees

- **Zero-SSRF / 100% Offline URL Analysis:** Submitted URLs are evaluated purely in-memory using static lexical, structural, and Shannon entropy analysis. The server **NEVER** executes HTTP/HTTPS requests, DNS lookups, redirect tracking, or browser automation on target URLs.
- **Explainable Rules Engine:** Combines machine learning predictions (when artifacts are present) with deterministic, human-readable threat rules (e.g. OTP solicitation, remote access lures, brand domain spoofing, authority `@` deception).
- **Multi-Modal Risk Fusion:** Dynamically normalizes risk weights across available signals (Text, URL, Rules Engine) without treating missing inputs as safe.
- **Privacy & Sensitive Data Masking:** Automatically redacts credit cards, OTPs, PINs, passwords, UPI handles, and sensitive query tokens from log streams and previews.
- **Hardened Security Controls:** Application-layer rate limiting (`slowapi`), strict production CORS enforcement, security response headers, and standardized error envelopes.

---

## 2. Architecture & Request Pipeline

```
                        [ Client Request ]
                                │
                                ▼
                       [ FastAPI Router ]
                                │
                                ▼
                 [ Input Validation (Pydantic) ]
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
 [ Text Analyzer ]                              [ URL Analyzer ]
 (Keywords, Urgency, Caps,              (Lexical / Entropy Features,
   TF-IDF + LogReg Model*)                    Random Forest Model*)
        │                                               │
        └───────────────────────┬───────────────────────┘
                                ▼
                     [ Rules Engine Evaluator ]
               (Deterministic patterns, Brand mismatch,
                IP host, Authority @ deception)
                                │
                                ▼
                      [ Risk Fusion Engine ]
                (Weighted multi-modal normalization,
                 Critical escalation, Action advice)
                                │
                                ▼
                 [ Explainable JSON Response ]
```

*\* Note: Machine learning models (TF-IDF + Logistic Regression for text, Random Forest for URLs) are integrated via adapter interfaces. In the absence of trained `.joblib` model artifacts, the system operates transparently using deterministic heuristics and rules without fabricating ML predictions.*

---

## 3. Technology Stack & Requirements

- **Runtime:** Python 3.10+ (Tested on Python 3.13)
- **Framework:** FastAPI `>=0.110.0`
- **ASGI Web Server:** Uvicorn `[standard] >=0.28.0`
- **Validation & Settings:** Pydantic `v2` (`>=2.6.0`) & `pydantic-settings` (`>=2.2.0`)
- **Data & Feature Processing:** `numpy`, `pandas`, `scipy`, `scikit-learn`, `joblib`, `tldextract`, `validators`
- **Rate Limiting:** `slowapi` (`>=0.1.10`)
- **Testing & Client:** `pytest`, `pytest-asyncio`, `httpx`

---

## 4. Project Directory Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI factory, CORS, Rate Limiters & exception handlers
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── analyze.py       # Analysis routes (/text, /url, /combined, /qr)
│   │       ├── feedback.py      # User feedback reporting route (/feedback)
│   │       └── system.py        # Health & model info routes (/health, /model-info)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analyze.py           # Pydantic analysis request/response schemas & enums
│   │   ├── feedback.py          # Feedback request and response schemas
│   │   └── response.py          # Standardized error envelopes & health schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── text_analyzer.py     # Text threat regex, heuristics & ML adapter interface
│   │   ├── url_analyzer.py      # In-memory lexical feature analysis
│   │   ├── url_extractor.py     # URL & payment URI extraction from raw text
│   │   ├── rules_engine.py      # Deterministic explainable rules engine
│   │   ├── risk_fusion.py       # Multi-modal risk fusion engine
│   │   └── model_service.py     # Centralized singleton orchestration service
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── base_model.py        # Abstract base class for ML model adapters
│   │   ├── text_model.py        # TF-IDF + Logistic Regression adapter
│   │   └── url_model.py         # Lexical Random Forest adapter
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic environment configuration & CORS validator
│   │   ├── limiter.py           # Slowapi rate limiter instance & client IP extractor
│   │   ├── logging.py           # Structured JSON logger with masking filter
│   │   └── security.py          # Security HTTP headers middleware & text sanitizer
│   └── utils/
│       ├── __init__.py
│       ├── masking.py           # Redaction utilities for OTPs, PINs, cards, UPI IDs
│       └── url_utils.py         # Offline TLDExtract & Shannon entropy calculator
├── models/                      # Folder for placing trained model artifacts (.joblib)
│   ├── text/
│   └── url/
├── tests/                       # Pytest test suite (150+ unit/integration/security tests)
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore file
├── requirements.txt             # Dependency specification
├── API.md                       # Comprehensive API specification
├── ARCHITECTURE.md              # Pipeline & risk fusion architectural documentation
├── ML_INTEGRATION.md            # ML Engineer artifact integration guide
├── SECURITY.md                  # Security controls & hardening documentation
└── README.md                    # Main repository readme
```

---

## 5. Installation & Setup

### 1. Environment Prerequisites
Ensure Python 3.10+ is installed:
```bash
python --version
```

### 2. Virtual Environment Setup
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 6. Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Configuration Variables Summary

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `LinkSentry Backend` | Application title |
| `APP_VERSION` | `1.0.0` | Semantic version string |
| `ENVIRONMENT` | `development` | Runtime mode (`development`, `production`) |
| `API_PREFIX` | `/api` | Root API path prefix |
| `TEXT_MODEL_PATH` | `""` | Path to trained text classifier `.joblib` artifact |
| `TEXT_VECTORIZER_PATH` | `""` | Path to trained TF-IDF vectorizer `.joblib` artifact |
| `URL_MODEL_PATH` | `""` | Path to trained Random Forest `.joblib` artifact |
| `TEXT_WEIGHT` | `0.45` | Default fusion weight for text analysis |
| `URL_WEIGHT` | `0.35` | Default fusion weight for URL analysis |
| `RULE_WEIGHT` | `0.20` | Default fusion weight for rules engine |
| `MAX_TEXT_LENGTH` | `10000` | Maximum character limit for text inputs |
| `MAX_URL_LENGTH` | `4096` | Maximum character limit for URL inputs |
| `RATE_LIMIT_ENABLED` | `true` | Enable application-layer rate limiting |
| `RATE_LIMIT_ANALYZE` | `60/minute` | Rate limit for analysis endpoints |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Comma-separated list of allowed CORS origins |

---

## 7. Running the Application

Launch the development server using Uvicorn:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Interactive API Documentation
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)

---

## 8. Running Automated Tests

Run the complete automated test suite (including unit, pipeline, security, and QA scenarios):
```bash
d:\LinkSentry\Backend\.venv\Scripts\pytest -v
```

To run quietly with execution duration profiling:
```bash
d:\LinkSentry\Backend\.venv\Scripts\pytest -q --durations=10
```

---

## 9. Further Documentation

- 📄 [API Specification](file:///d:/LinkSentry/Backend/API.md)
- 📄 [Architecture & Fusion Guide](file:///d:/LinkSentry/Backend/ARCHITECTURE.md)
- 📄 [ML Artifact Integration Guide](file:///d:/LinkSentry/Backend/ML_INTEGRATION.md)
- 📄 [Security & Hardening Policy](file:///d:/LinkSentry/Backend/SECURITY.md)
