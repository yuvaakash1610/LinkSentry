# LinkSentry Backend — Security Policy & Hardening Documentation

This document outlines the security architecture, privacy controls, zero-SSRF guarantees, and hardening configurations enforced across the LinkSentry backend.

---

## 1. Zero-SSRF & Passive URL Analysis Guarantee

LinkSentry is designed for safe evaluation of untrusted, malicious, or unknown URLs submitted by end users.

### Critical Security Protections
- **No Remote Fetching:** The application **NEVER** executes `requests.get()`, `httpx.get()`, `urllib.request`, `socket`, `dns`, `aiohttp`, `selenium`, `pyppeteer`, or `playwright` calls against submitted URLs.
- **No DNS Lookups:** Target hostnames are never queried against DNS resolution servers.
- **No Browser Automation / Execution:** Submitted links are never loaded, rendered, or executed in web browsers or headless environments.
- **Static In-Memory Parsing:** All URL features (length, entropy, structural tokens, homoglyphs, subdomains, TLDs) are extracted purely in-memory using string parsing (`urllib.parse`, `ipaddress`, regex, and offline `tldextract`).

---

## 2. Offline-Only `tldextract` Hardening

To prevent `tldextract` from attempting remote public suffix list downloads or HTTP calls over the network, `tldextract` is explicitly initialized with an empty suffix list URL tuple across all services:

```python
# app/utils/url_utils.py
offline_extractor = tldextract.TLDExtract(suffix_list_urls=())
```

- **Guaranteed Behavior:** Uses only local package-bundled public suffix data.
- **Network Isolation:** Zero background network requests or HTTP fallback updates.

---

## 3. Data Privacy & Credential Masking

User-submitted messages and URLs may contain sensitive personal data, credit cards, OTPs, PINs, or credentials. LinkSentry prevents raw PII leakage into log streams or response payloads.

### Masking Utilities (`app/utils/masking.py`)
- **Payment Card Redaction:** Card numbers (13-19 digits) are masked, leaving only the last 4 digits visible (`***-***-***-1049`).
- **CVV / PIN / OTP Redaction:** Regex patterns redact CVVs (`[REDACTED_CVV]`), PINs (`[REDACTED_PIN]`), OTPs (`[REDACTED_OTP]`), and passwords (`[REDACTED_PWD]`).
- **URL Parameter Redaction:** Sensitive query parameters (`token`, `access_token`, `secret`, `password`, `key`, `auth`, `session`) are sanitized prior to logging (`token=[REDACTED]`).
- **URL Authority Redaction:** Embedded user credentials (`http://user:pass@host`) are stripped prior to rule evaluation.

---

## 4. Application Rate Limiting

To prevent API flooding and denial-of-service (DoS) attacks on public analysis endpoints, application-layer rate limiting is enforced via `slowapi` (`app/core/limiter.py` & `app/main.py`).

### Protected Endpoints
- `POST /api/analyze/text`
- `POST /api/analyze/url`
- `POST /api/analyze/combined`
- `POST /api/analyze/qr`

### Configuration Settings (`.env`)
```ini
RATE_LIMIT_ENABLED=true
RATE_LIMIT_ANALYZE=60/minute
```

### Exceeded Limit Payload (`429 Too Many Requests`)
When client rate limits are exceeded, the API returns a standard JSON error envelope without stack traces or sensitive user data:
```json
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Rate limit exceeded. Please try again later.",
    "request_id": "801193ed-8a75-416f-95dc-373af1cf346b"
  }
}
```

---

## 5. Production CORS Hardening

Cross-Origin Resource Sharing (CORS) is managed via Pydantic model validation (`app/core/config.py`) and FastAPI middleware (`app/main.py`).

### Strict Rules Enforced
1. **Production Fail-Fast (`ENVIRONMENT=production`):**
   - Startup fails fast (`ValueError`) if `ALLOWED_ORIGINS` is missing or empty.
   - Startup fails fast (`ValueError`) if wildcard origin `"*"` is configured in production.
   - Requires explicit `http://` or `https://` origin schemes.
2. **Development Mode (`ENVIRONMENT=development`):**
   - Allows specified local development origins (`http://localhost:3000`, `http://localhost:8000`).
   - If wildcard `"*"` is used in development, `allow_credentials` is automatically disabled (`False`) to prevent browser credential rejection.

---

## 6. Secrets & Environment Isolation

- Configuration settings are loaded exclusively via Pydantic `BaseSettings` (`app/core/config.py`).
- Source code contains **zero hardcoded secrets**, API keys, or production passwords.
- `.env` files containing local environment values are explicitly ignored in [`.gitignore`](file:///d:/LinkSentry/Backend/.gitignore).

---

## 7. Security HTTP Headers & Exception Envelopes

### Security Headers Middleware (`app/core/security.py`)
All HTTP responses automatically include OWASP-recommended security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Exception Traceback Prevention
- Exception handlers (`app/main.py`) intercept `RequestValidationError`, `HTTPException`, and uncaught exceptions.
- Responses return clean JSON error envelopes containing request correlation IDs.
- Raw Python stack traces or server file paths are **never** exposed to clients.

---

## 8. HTTPS Production Deployment Checklist

When deploying LinkSentry to a production environment:

1. **Reverse Proxy & TLS Termination:** Deploy behind a secure reverse proxy (e.g. Nginx, Caddy, or AWS ALB) enforcing HTTPS with valid TLS certificates.
2. **Infrastructure WAF / Rate Limiting:** Complement application-level rate limits with edge protection (e.g. Cloudflare WAF, Nginx `limit_req`) to mitigate volumetric network DDoS attacks.
3. **Set Environment Variables:**
   ```ini
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://app.linksentry.io,https://admin.linksentry.io
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_ANALYZE=60/minute
   ```
4. **Isolated Service Container:** Run Uvicorn worker processes inside unprivileged containers (e.g. Docker non-root user).
