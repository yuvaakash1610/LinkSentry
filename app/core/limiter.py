from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_client_ip(request) -> str:
    """
    Extract client IP address safely for rate limiting.
    Evaluates X-Forwarded-For if present behind proxy, falling back to remote host address.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[],
)
