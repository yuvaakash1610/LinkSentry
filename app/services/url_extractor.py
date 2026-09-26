import re
from typing import List
from app.utils.url_utils import offline_extractor

# Standard URL pattern for explicit schemes (http, https, ftp, upi)
SCHEME_URL_REGEX = re.compile(
    r"\b(?:https?|ftp|upi)://[^\s<>\"'{}|\\^`\[\]]+",
    re.IGNORECASE,
)

# Pattern for schemeless URLs (e.g. www.domain.com or domain.tld/path)
SCHEMELESS_URL_REGEX = re.compile(
    r"\b(?:www\.)[a-zA-Z0-9.\-_]+\.[a-zA-Z]{2,}(?:/[^\s<>\"'{}|\\^`\[\]]*)?",
    re.IGNORECASE,
)


def extract_urls(text: str) -> List[str]:
    """
    Extract all distinct URLs and payment URIs from raw text or message content.
    Returns cleaned, deduplicated URLs preserving order of occurrence.
    """
    if not text:
        return []

    found_urls: List[str] = []
    seen = set()

    # Match URLs with schemes
    for match in SCHEME_URL_REGEX.finditer(text):
        raw_url = match.group(0).rstrip(".,;!?:)'\"]}")
        if raw_url not in seen:
            seen.add(raw_url)
            found_urls.append(raw_url)

    # Match schemeless URLs
    for match in SCHEMELESS_URL_REGEX.finditer(text):
        raw_url = match.group(0).rstrip(".,;!?:)'\"]}")
        if raw_url not in seen:
            # Check if valid domain using centralized offline extractor
            ext = offline_extractor(raw_url)
            if ext.domain and ext.suffix:
                seen.add(raw_url)
                found_urls.append("https://" + raw_url)

    return found_urls

