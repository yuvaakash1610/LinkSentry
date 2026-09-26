# LinkSentry Backend — API Specification

This document provides a comprehensive API specification for all routes exposed by the LinkSentry Backend.

All analysis and utility endpoints are prefixed by default with `/api` (configurable via `API_PREFIX`).

---

## Standard Error Response Schema

All error responses across all endpoints adhere to a standardized JSON error envelope:

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Text cannot be empty or whitespace-only.",
    "request_id": "801193ed-8a75-416f-95dc-373af1cf346b"
  }
}
```

### Standard HTTP Status & Error Codes

| Status Code | Error Code | Description |
| :--- | :--- | :--- |
| `400 Bad Request` | `BAD_REQUEST` | Malformed request or invalid parameters |
| `422 Unprocessable` | `INVALID_INPUT` | Input validation failure (length, scheme, JSON schema) |
| `429 Too Many` | `TOO_MANY_REQUESTS` | Application-level rate limit exceeded |
| `500 Internal Error` | `INTERNAL_SERVER_ERROR` | Unexpected server failure |

---

## 1. System Health Check

### Endpoint: `GET /api/health` (also accessible at `/health`)

* **Purpose:** Verify server operational health and service version without exposing internal server paths or environment secrets.
* **Authentication / Rate Limit:** None (bypasses rate limiting).
* **Request Format:** No parameters or request body required.

#### Response Format (`200 OK`)
```json
{
  "status": "ok",
  "service": "linksentry-backend",
  "version": "1.0.0"
}
```

#### Validation & Errors
- Always returns `200 OK` when the service process is active.

---

## 2. Model Metadata & Status

### Endpoint: `GET /api/model-info` (also accessible at `/model-info`)

* **Purpose:** Retrieve current availability, version, and architecture status of ML model adapters without exposing local host file paths.
* **Authentication / Rate Limit:** None (bypasses rate limiting).
* **Request Format:** No parameters or request body required.

#### Response Format (`200 OK`)
```json
{
  "text_model": {
    "name": "TF-IDF + Logistic Regression",
    "version": "1.0.0",
    "status": "unavailable"
  },
  "url_model": {
    "name": "Lexical Random Forest",
    "version": "1.0.0",
    "status": "unavailable"
  }
}
```

#### Validation & Errors
- Status will be `"available"` / `"active"` if valid trained `.joblib` model artifacts are present on disk, or `"unavailable"` if artifacts are missing.

---

## 3. Analyze Message Text

### Endpoint: `POST /api/analyze/text`

* **Purpose:** Analyze suspicious SMS messages, email text, or notification snippets for scam patterns, urgency manipulation, and credential solicitation.
* **Rate Limit:** Protected by `RATE_LIMIT_ANALYZE` (Default: `60/minute`).

#### Request Schema (`TextAnalysisRequest`)

| Field | Type | Required | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `text` | `string` | **Yes** | — | `1` to `10000` chars; non-empty & non-whitespace |
| `source` | `string` | No | `"manual_paste"` | Origin source identifier |
| `language_hint` | `string` | No | `"en"` | Expected ISO language code |

#### Example Request
```json
{
  "text": "URGENT: Your NetBanking account is blocked. Share your OTP 654321 with our executive immediately.",
  "source": "sms",
  "language_hint": "en"
}
```

#### Example Response (`200 OK`)
```json
{
  "request_id": "42c3d526-9e67-4d7a-8f55-12b7a957b420",
  "risk_score": 0.80,
  "risk_level": "high_risk",
  "category": "credential_harvesting",
  "confidence": 0.85,
  "reasons": [
    "Identified account suspension/blocking threat.",
    "Identified credential or OTP solicitation.",
    "Identified coercive urgency pressure."
  ],
  "indicators": [
    "txt_account_suspension",
    "txt_credential_solicitation",
    "txt_coercive_urgency"
  ],
  "model_status": "unavailable",
  "rules_triggered": [
    "TXT_ACCOUNT_SUSPENSION",
    "TXT_CREDENTIAL_SOLICITATION",
    "TXT_COERCIVE_URGENCY"
  ],
  "extracted_urls": [],
  "recommended_action": "Do not click the link or provide credentials, OTPs, PINs, or payment details."
}
```

#### Error Example (`422 Unprocessable Content`)
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "body -> text: Text cannot be empty or whitespace-only.",
    "request_id": "801193ed-8a75-416f-95dc-373af1cf346b"
  }
}
```

---

## 4. Analyze Suspicious URL

### Endpoint: `POST /api/analyze/url`

* **Purpose:** Analyze a suspicious URL string using 100% in-memory static lexical, structural, and Shannon entropy heuristics without remote network fetching.
* **Rate Limit:** Protected by `RATE_LIMIT_ANALYZE` (Default: `60/minute`).

#### Request Schema (`UrlAnalysisRequest`)

| Field | Type | Required | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `url` | `string` | **Yes** | — | `1` to `4096` chars; supported schemes: `http`, `https`, `ftp`, `upi` |
| `source` | `string` | No | `"manual_paste"` | Origin source identifier |

#### Example Request
```json
{
  "url": "http://sbi.verify-portal.top/login?session=abc",
  "source": "browser_intercept"
}
```

#### Example Response (`200 OK`)
```json
{
  "url": "http://sbi.verify-portal.top/login?session=abc",
  "risk_score": 0.65,
  "risk_level": "suspicious",
  "hostname": "sbi.verify-portal.top",
  "registered_domain": "verify-portal.top",
  "indicators": [
    "suspicious_tld",
    "brand_domain_mismatch"
  ],
  "extracted_features": {
    "url_length": 46,
    "hostname_length": 21,
    "has_suspicious_tld": true,
    "is_ip_host": false,
    "is_shortener": false,
    "subdomain_count": 2,
    "url_entropy": 4.1205
  },
  "model_prediction": null,
  "confidence": 0.85,
  "model_status": "unavailable",
  "triggered_rules": [
    "RULE_SUSPICIOUS_URL",
    "RULE_BRAND_DOMAIN_MISMATCH"
  ],
  "claimed_brand": "sbi",
  "brand_domain_mismatch": true,
  "is_ip_host": false,
  "is_shortener": false
}
```

---

## 5. Analyze Combined Message & URLs

### Endpoint: `POST /api/analyze/combined`

* **Purpose:** Jointly evaluate textual context alongside associated URL strings for correlated cybersecurity threats and multi-modal risk fusion.
* **Rate Limit:** Protected by `RATE_LIMIT_ANALYZE` (Default: `60/minute`).

#### Request Schema (`CombinedAnalysisRequest`)

| Field | Type | Required | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `text` | `string` | No* | `null` | Max `10000` chars |
| `urls` | `array[string]` | No* | `[]` | List of URL strings |
| `url` | `string` | No* | `null` | Single URL string alias |
| `source` | `string` | No | `"manual_paste"` | Submission source |
| `language_hint` | `string` | No | `"en"` | ISO language code |

*\* Validation Constraint: At least `text` OR at least one `url` must be provided.*

#### Example Request
```json
{
  "text": "URGENT: Your SBI account is suspended. Update KYC at http://sbi.verify-portal.top/login immediately.",
  "urls": [
    "http://sbi.verify-portal.top/login"
  ],
  "source": "sms"
}
```

#### Example Response (`200 OK`)
```json
{
  "request_id": "c1f8a847-194b-4b13-a4e9-11f847a95612",
  "final_risk_score": 0.85,
  "final_risk_level": "high_risk",
  "text_analysis": {
    "risk_score": 0.80,
    "risk_level": "high_risk",
    "category": "credential_harvesting",
    "confidence": 0.85,
    "rules_triggered": ["TXT_ACCOUNT_SUSPENSION", "TXT_KYC_LURE"]
  },
  "url_analysis": [
    {
      "url": "http://sbi.verify-portal.top/login",
      "risk_score": 0.65,
      "risk_level": "suspicious",
      "triggered_rules": ["RULE_SUSPICIOUS_URL", "RULE_BRAND_DOMAIN_MISMATCH"]
    }
  ],
  "rules_triggered": [
    "TXT_ACCOUNT_SUSPENSION",
    "TXT_KYC_LURE",
    "RULE_SUSPICIOUS_URL",
    "RULE_BRAND_DOMAIN_MISMATCH"
  ],
  "recommended_action": "Do not click the link or provide credentials, OTPs, PINs, or payment details.",
  "summary": "High risk detected with critical indicators of scam or phishing patterns."
}
```

---

## 6. Analyze QR Code Content

### Endpoint: `POST /api/analyze/qr`

* **Purpose:** Evaluate raw decoded payload strings (URLs, payment URIs, text) obtained from Android QR code camera scans.
* **Rate Limit:** Protected by `RATE_LIMIT_ANALYZE` (Default: `60/minute`).

#### Request Schema (`QrAnalysisRequest`)

| Field | Type | Required | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `content` | `string` | No* | `null` | Max `10000` chars |
| `payload` | `string` | No* | `null` | Alias for `content` |
| `source` | `string` | No | `"qr"` | Origin identifier |

*\* Validation Constraint: Either `content` or `payload` must be non-empty.*

#### Example Request
```json
{
  "content": "upi://pay?pa=scammer@upi&pn=FakeMerchant&am=5000",
  "source": "qr"
}
```

#### Example Response (`200 OK`)
```json
{
  "request_id": "d718a943-4122-4467-8912-110034a78190",
  "final_risk_score": 0.20,
  "final_risk_level": "low",
  "text_analysis": null,
  "url_analysis": [
    {
      "url": "upi://pay?pa=scammer@upi&pn=FakeMerchant&am=5000",
      "risk_score": 0.20,
      "risk_level": "low",
      "hostname": "",
      "registered_domain": "",
      "triggered_rules": []
    }
  ],
  "rules_triggered": [],
  "recommended_action": "Continue normally, while remaining cautious.",
  "summary": "No immediate high-risk indicators detected."
}
```

---

## 7. Submit Detection Feedback

### Endpoint: `POST /api/feedback`

* **Purpose:** Submit user or app feedback (`correct`, `incorrect`, `uncertain`) and category classifications (`FALSE_POSITIVE`, `FALSE_NEGATIVE`) to improve security intelligence.
* **Rate Limit:** Standard application handling.

#### Request Schema (`FeedbackRequest`)

| Field | Type | Required | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `feedback` | `string` | No* | `null` | Enum: `correct`, `incorrect`, `uncertain` |
| `category` | `string` | No* | `null` | Enum: `FALSE_POSITIVE`, `FALSE_NEGATIVE`, `USER_CORRECTION`, `GENERAL` |
| `request_id` | `string` | No | `null` | Request correlation ID being reviewed |
| `reported_risk_tier` | `string` | No | `null` | Assigned risk level |
| `input_text` | `string` | No | `null` | Optional submitted text (automatically masked) |
| `input_url` | `string` | No | `null` | Optional submitted URL (automatically masked) |
| `user_notes` | `string` | No | `null` | Optional user notes (max `2000` chars) |

*\* Validation Constraint: At least `feedback` OR `category` must be provided.*

#### Example Request
```json
{
  "feedback": "incorrect",
  "category": "FALSE_POSITIVE",
  "request_id": "c1f8a847-194b-4b13-a4e9-11f847a95612",
  "reported_risk_tier": "high_risk",
  "user_notes": "This notification was from my verified bank app."
}
```

#### Example Response (`200 OK`)
```json
{
  "status": "success",
  "feedback_id": "e4a819b0-9012-45e2-b123-998811002233",
  "message": "Thank you for helping keep LinkSentry accurate and secure."
}
```
