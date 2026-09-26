import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from typing import Optional

# Pre-compiled regular expressions for sensitive pattern detection

# Credit / Debit Cards (13-19 digits, allowing optional spaces or hyphens)
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# CVV / CVC (3 or 4 digits near cvv/cvc indicators)
CVV_PATTERN = re.compile(
    r"\b(?:cvv|cvc|cvv2|cvc2|security\s*code)(?:\s+(?:is|was))?[\s:=]+(\d{3,4})\b",
    re.IGNORECASE,
)

# PIN (4 to 6 digit security PINs)
PIN_PATTERN = re.compile(
    r"\b(?:pin|atm\s*pin|security\s*pin)(?:\s+(?:is|was))?[\s:=]+(\d{4,6})\b",
    re.IGNORECASE,
)

# OTP / Verification Codes (4 to 8 digits near otp/code/verification)
OTP_PATTERN = re.compile(
    r"\b(?:otp|one\s*time\s*password|verification\s*code|auth\s*code|passcode)(?:\s+(?:is|was))?[\s:=]+(\d{4,8})\b",
    re.IGNORECASE,
)

# General standalone 6-digit OTP codes in message texts
STANDALONE_OTP_PATTERN = re.compile(r"\b\d{6}\b")

# Passwords in key-value format
PASSWORD_PATTERN = re.compile(
    r"\b(?:password|passwd|pwd|pass)(?:\s+(?:is|was))?[\s:=]+([^\s,;]+)",
    re.IGNORECASE,
)

# UPI IDs (common payment handles, e.g., user@okhdfcbank, 9876543210@paytm, name@upi)
UPI_PATTERN = re.compile(r"\b[a-zA-Z0-9.\-_]{2,100}@[a-zA-Z0-9]{2,40}\b")

# Common sensitive URL query parameter names
SENSITIVE_QUERY_PARAMS = {
    "token",
    "access_token",
    "auth_token",
    "refresh_token",
    "key",
    "apikey",
    "api_key",
    "secret",
    "secret_key",
    "password",
    "pwd",
    "pass",
    "otp",
    "pin",
    "cvv",
    "session",
    "session_id",
    "sid",
    "code",
    "auth",
}


def mask_card_number(text: str) -> str:
    """Mask payment card numbers, leaving only the last 4 digits visible."""
    def _replace_card(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19:
            return f"***-***-***-{digits[-4:]}"
        return match.group(0)

    return CARD_PATTERN.sub(_replace_card, text)


def mask_sensitive_text(text: Optional[str]) -> str:
    """
    Scrub sensitive credentials, financial identifiers, and secrets from text.
    
    Ensures safe handling for logging and audit trails without persisting
    raw OTPs, PINs, card numbers, passwords, or UPI handles.
    """
    if not text:
        return ""

    sanitized = text

    # Redact CVVs
    sanitized = CVV_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_CVV]"), sanitized)

    # Redact PINs
    sanitized = PIN_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_PIN]"), sanitized)

    # Redact OTPs
    sanitized = OTP_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_OTP]"), sanitized)

    # Redact Passwords
    sanitized = PASSWORD_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_PWD]"), sanitized)

    # Redact Card numbers
    sanitized = mask_card_number(sanitized)

    # Redact UPI IDs
    sanitized = UPI_PATTERN.sub("[REDACTED_UPI]", sanitized)

    return sanitized


def mask_sensitive_url_params(url_str: Optional[str]) -> str:
    """
    Mask sensitive URL query parameters (tokens, keys, secrets, session IDs).
    """
    if not url_str:
        return ""

    try:
        parsed = urlparse(url_str)
        if not parsed.query:
            return url_str

        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        masked_pairs = []
        for key, value in query_pairs:
            if key.lower() in SENSITIVE_QUERY_PARAMS or any(
                sens in key.lower() for sens in ("token", "secret", "pass", "key")
            ):
                masked_pairs.append((key, "[REDACTED]"))
            else:
                masked_pairs.append((key, value))

        new_query = urlencode(masked_pairs)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))
    except Exception:
        # Fallback safe representation if unparseable
        return "[UNPARSEABLE_URL]"
