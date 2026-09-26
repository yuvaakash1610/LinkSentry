from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Default max content length: 2MB to protect against DoS attacks
MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces standard security headers across all responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def sanitize_input_string(text: str, max_length: int) -> str:
    """
    Sanitize and truncate incoming text strings to designated safety bounds.
    """
    if not text:
        return ""
    # Strip null bytes and non-printable control characters (except newline, tab, carriage return)
    cleaned = "".join(
        ch for ch in text if ch in ("\n", "\r", "\t") or (ch.isprintable() and ch != "\x00")
    )
    return cleaned[:max_length].strip()
