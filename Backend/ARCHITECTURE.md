# LinkSentry Backend — Architecture & Risk Fusion Specification

This document details the internal architecture, modular pipelines, and multi-modal risk fusion engine of the LinkSentry backend.

---

## 1. End-to-End Processing Pipeline

The LinkSentry backend processes untrusted user payloads through a strictly unidirectional, passive analytical pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Android Application                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP POST Payload (JSON)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Routing & Middleware                       │
│  - Correlation ID Generation (X-Request-ID)                             │
│  - Application-Layer Rate Limiting (Slowapi)                            │
│  - CORS & Security Headers Middleware                                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Input Validation (Pydantic)                        │
│  - Schema enforcement (Text max 10k, URL max 4096)                       │
│  - Non-empty & whitespace-only validation                               │
│  - URL Scheme validation (http, https, ftp, upi)                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Analysis Services                             │
│  ┌──────────────────────────────┐     ┌──────────────────────────────┐  │
│  │    Text Analyzer Service     │     │     URL Analyzer Service     │  │
│  │ - Threat Pattern Regex       │     │ - Lexical & Entropy Features │  │
│  │ - Uppercase & Punctuation    │     │ - Offline TLDExtract         │  │
│  └──────────────┬───────────────┘     └──────────────┬───────────────┘  │
└─────────────────┼────────────────────────────────────┼──────────────────┘
                  │                                    │
                  ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           ML Model Adapters                             │
│  ┌──────────────────────────────┐     ┌──────────────────────────────┐  │
│  │  Text Model Adapter (TF-IDF) │     │ URL Model (Random Forest)    │  │
│  │ - Returns predict() probability│    │ - Returns predict() prob     │  │
│  └──────────────┬───────────────┘     └──────────────┬───────────────┘  │
└─────────────────┼────────────────────────────────────┼──────────────────┘
                  │                                    │
                  └──────────────────┬─────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Rules Engine Evaluator                          │
│  - Evaluates deterministic rules (OTP request, Remote access, IP host, │
│    brand domain mismatch, authority @ deception)                        │
│  - Generates explainable RuleMatch reasons & normalized scores          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Risk Fusion Engine                            │
│  - Weighted multi-modal normalization across available signals          │
│  - Missing input weight adjustment (never treats missing as safe)       │
│  - Critical rule escalation (escalates severe indicators)              │
│  - Maps score to discrete RiskLevel & PRD Recommended Action            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Explainable JSON Response                         │
│  (final_risk_score, final_risk_level, sub-analyses, rules_triggered,   │
│   recommended_action, summary, request_id)                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Layer Breakdown

### 2.1 API & Middleware Layer (`app/api/`, `app/main.py`)
- **FastAPI Framework:** Handles asynchronous routing, OpenAPI schema generation, and exception mapping.
- **Correlation ID Middleware:** Assigns or preserves a unique UUID `X-Request-ID` across logging records and response headers.
- **Rate Limiting (`app/core/limiter.py`):** Utilizes `slowapi` to enforce IP-based rate limits on analysis endpoints without persisting IP histories or raw request payloads.

### 2.2 Validation Layer (`app/schemas/analyze.py`)
- Enforces strict Pydantic `v2` field validation and length boundaries before execution enters the service layer.
- Performs URL scheme verification against allowed schemes (`http`, `https`, `ftp`, `upi`).

### 2.3 Text Analyzer (`app/services/text_analyzer.py`)
- Evaluates text messages against semantic threat regex patterns (`TEXT_THREAT_PATTERNS`).
- Calculates heuristic urgency indicators (excessive uppercase lettering, aggressive punctuation).
- Integrates with `TextMLModel` adapter (70% ML score + 30% heuristic score when ML artifact is available).

### 2.4 URL Analyzer (`app/services/url_analyzer.py` & `app/utils/url_utils.py`)
- Performs **100% static, in-memory** feature extraction:
  - Shannon Entropy of hostname and full URL string.
  - IP host classification (IPv4, IPv6, private/loopback).
  - Authority `@` sign deception detection.
  - Punycode IDN homoglyph detection (`xn--`).
  - Offline TLD and public suffix extraction via `tldextract.TLDExtract(suffix_list_urls=())`.
  - Brand domain mismatch evaluation against `KNOWN_BRAND_DOMAINS`.

### 2.5 ML Adapter Architecture (`app/ml/`)
- Implements abstract base class `BaseModel` (`app/ml/base_model.py`).
- Pluggable adapters (`TextMLModel`, `UrlMLModel`) wrap `joblib.load()`.
- When trained artifacts are missing or corrupt, adapters safely return `(None, False)` and report `model_status: "unavailable"`, allowing the system to operate transparently via rule heuristics.

### 2.6 Deterministic Rules Engine (`app/services/rules_engine.py`)
- Evaluates deterministic, human-readable cybersecurity rules:
  - `RULE_OTP_REQUEST`: Solicitation of OTPs/PINs.
  - `RULE_REMOTE_ACCESS`: Requests for remote control tools (AnyDesk, TeamViewer).
  - `RULE_ACCOUNT_THREAT`: Account suspension or card blocking threats.
  - `RULE_URGENCY_PAYMENT`: Coercive urgent payment demands.
  - `RULE_SUSPICIOUS_URL`: High-abuse TLDs (`.xyz`, `.top`, `.work`, etc.).
  - `RULE_BRAND_DOMAIN_MISMATCH`: Brand claim on unrelated registered domain.
  - `RULE_IP_HOST`: Host is a raw IP address.
  - `RULE_AT_DECEPTION`: Authority contains `@` deception.
  - `CORR_SHORTENER_URGENT_MSG`: Combined shortened URL + urgent text lure.

---

## 3. Multi-Modal Risk Fusion Engine

The `RiskFusionService` (`app/services/risk_fusion.py`) combines independent sub-analysis risk scores into a unified, explainable threat assessment.

### 3.1 Configurable Fusion Weights

Default configurable weights loaded from application configuration:
- `TEXT_WEIGHT` = `0.45`
- `URL_WEIGHT` = `0.35`
- `RULE_WEIGHT` = `0.20`

### 3.2 Missing Input Normalization

The fusion engine knows which signals are actually present. To ensure missing inputs (e.g. text-only or URL-only analysis) are **never treated as safe**, weights are dynamically normalized across available signals:

$$\text{WeightSum} = \sum_{i \in \text{Available}} W_i$$

$$\text{FinalScore} = \min\left(1.0, \frac{(S_{\text{text}} \cdot W_{\text{text}}) + (S_{\text{url}} \cdot W_{\text{url}}) + (S_{\text{rules}} \cdot W_{\text{rules}})}{\text{WeightSum}}\right)$$

Where:
- $S_{\text{text}}$ = Risk score from Text Analyzer (if text provided).
- $S_{\text{url}}$ = Maximum risk score across evaluated URLs (if URLs provided).
- $S_{\text{rules}}$ = Accumulated normalized score from Rules Engine (if rules matched).

### 3.3 Risk Level Mapping Thresholds

The continuous risk score $[0.00, 1.00]$ is mapped to discrete LinkSentry risk tiers:

| Score Range | Risk Level | Action Advisory |
| :--- | :--- | :--- |
| `0.00 - 0.29` | `low` | Continue normally, while remaining cautious. |
| `0.30 - 0.59` | `verify_independently` | Verify the request using an official source before taking action. |
| `0.60 - 0.79` | `suspicious` | Do not provide sensitive information or make a payment until independently verified. |
| `0.80 - 1.00` | `high_risk` | Do not click the link or provide credentials, OTPs, PINs, or payment details. |

### 3.4 Critical Risk Escalation Logic

Regardless of raw weighted scores, if any **critical rule ID** is triggered:
- Critical Rule Set: `RULE_OTP_REQUEST`, `RULE_REMOTE_ACCESS`, `RULE_IP_HOST`, `RULE_BRAND_DOMAIN_MISMATCH`, `TXT_UPI_COLLECT_SCAM`, `TXT_CREDENTIAL_SOLICITATION`, `TXT_ACCOUNT_SUSPENSION`, `URL_AT_DECEPTION`, `URL_IP_HOST`.
- **Escalation Rules:**
  1. If `FinalScore >= 0.50` and a critical rule triggered $\rightarrow$ Escalate level to `high_risk`.
  2. If `FinalScore < 0.50` (`low` or `verify_independently`) and a critical rule triggered $\rightarrow$ Escalate level to `suspicious`.
