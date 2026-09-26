import ipaddress
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlparse

import tldextract
import validators

# Explicitly disable remote suffix fetching to ensure 100% offline operation
offline_extractor = tldextract.TLDExtract(suffix_list_urls=())


# Known URL shortener domains
SHORTENER_DOMAINS: Set[str] = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "cutt.ly",
    "tiny.cc",
    "rb.gy",
    "shorturl.at",
    "v.gd",
    "clck.ru",
    "bl.ink",
    "rebrand.ly",
}

# TLDs frequently abused in phishing/scam campaigns
SUSPICIOUS_TLDS: Set[str] = {
    "xyz",
    "top",
    "work",
    "buzz",
    "click",
    "loan",
    "fit",
    "club",
    "online",
    "site",
    "icu",
    "monster",
    "rest",
    "gq",
    "cf",
    "tk",
    "ml",
    "ga",
}

# Suspicious keywords that may appear in phishing/scam paths or subdomains
SUSPICIOUS_KEYWORDS: List[str] = [
    "login",
    "verify",
    "kyc",
    "secure",
    "update",
    "claim",
    "reward",
    "account",
    "bank",
    "payment",
    "wallet",
    "refund",
]

# Curated mapping of targeted brands to their legitimate registered domains
# Ensures brand domain mismatch is detected without inventing mismatches
KNOWN_BRAND_DOMAINS: Dict[str, Set[str]] = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "onlinesbi.com"},
    "hdfc": {"hdfcbank.com", "hdfc.com"},
    "icici": {"icicibank.com"},
    "axis": {"axisbank.com"},
    "paytm": {"paytm.com"},
    "phonepe": {"phonepe.com"},
    "gpay": {"google.com"},
    "google": {"google.com"},
    "apple": {"apple.com", "icloud.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com"},
    "amazon": {"amazon.com", "amazon.in"},
    "netflix": {"netflix.com"},
    "paypal": {"paypal.com"},
    "facebook": {"facebook.com", "fb.com"},
    "instagram": {"instagram.com"},
    "whatsapp": {"whatsapp.com"},
    "epfo": {"epfindia.gov.in"},
    "aadhaar": {"uidai.gov.in"},
}


def normalize_url(url: str) -> str:
    """Normalize and sanitize URL string without network calls."""
    cleaned = url.strip()
    # Add scheme if missing for parsing purposes
    if not cleaned.startswith(("http://", "https://", "ftp://", "upi://")):
        cleaned = "https://" + cleaned
    return cleaned


def is_valid_url(url: str) -> bool:
    """Validate if input conforms to acceptable URL format without network calls."""
    normalized = normalize_url(url)
    return bool(validators.url(normalized))


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string (measures randomness/obfuscation)."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    freq: Dict[str, int] = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    for count in freq.values():
        prob = count / length
        entropy -= prob * math.log2(prob)
    return round(entropy, 4)


def inspect_ip_host(host_str: str) -> Tuple[bool, bool, bool, bool]:
    """
    Inspect whether the host is an IPv4 or IPv6 address.
    Returns: (is_ip, is_ipv4, is_ipv6, is_private_or_loopback)
    """
    clean_host = host_str.strip().strip("[]")
    if not clean_host:
        return False, False, False, False

    if clean_host.lower() == "localhost":
        return False, False, False, True

    # If it is an IPv4 with a trailing port (e.g. 192.168.1.1:8080), strip the port
    if ":" in clean_host and clean_host.count(":") == 1:
        clean_host = clean_host.split(":")[0]

    try:
        ip = ipaddress.ip_address(clean_host)
        is_ipv4 = isinstance(ip, ipaddress.IPv4Address)
        is_ipv6 = isinstance(ip, ipaddress.IPv6Address)
        is_priv = (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or str(ip).startswith("169.254.")  # Cloud metadata IP
        )
        return True, is_ipv4, is_ipv6, is_priv
    except ValueError:
        return False, False, False, False


def evaluate_brand_mismatch(
    registered_domain: str,
    domain: str,
    subdomain: str,
    path: str,
    userinfo: str,
) -> Tuple[Optional[str], bool]:
    """
    Determine if a brand name is claimed in authority/path while registered domain differs.
    Adheres strictly to 'Do not invent mismatches'.
    """
    reg_clean = registered_domain.lower()
    dom_clean = domain.lower()
    search_context = f"{userinfo} {subdomain} {path}".lower()

    for brand, legit_domains in KNOWN_BRAND_DOMAINS.items():
        # Case 1: Brand is the verified owner of the registered domain
        if reg_clean in legit_domains or dom_clean == brand:
            return brand, False

        # Case 2: Brand appears in userinfo, subdomain, or path of an unrelated domain
        if re.search(rf"\b{re.escape(brand)}\b", search_context):
            return brand, True

    return None, False


def is_ip_address(host: str) -> bool:
    """Check if the hostname is a raw IPv4 or IPv6 address."""
    is_ip, _, _, _ = inspect_ip_host(host)
    return is_ip


def extract_lexical_features(raw_url: str) -> Dict[str, Any]:
    """
    Extract comprehensive lexical, structural, and semantic characteristics of a URL string.
    
    GUARANTEE: 100% offline static string analysis. Zero network requests, zero DNS lookups.
    """
    normalized = normalize_url(raw_url)
    parsed = urlparse(normalized)

    # Deconstruct authority: check for @ deception
    full_netloc = parsed.netloc
    if "@" in full_netloc:
        userinfo, _, host_port = full_netloc.rpartition("@")
        has_at_deception = True
    else:
        userinfo = ""
        host_port = full_netloc
        has_at_deception = False

    # Extract clean host (without port or brackets)
    if host_port.startswith("[") and "]" in host_port:
        # IPv6 format e.g. [::1]:8080
        host = host_port[1 : host_port.index("]")]
    else:
        host = host_port.split(":")[0]
    host = host.lower()

    path = parsed.path
    query = parsed.query
    fragment = parsed.fragment
    scheme = parsed.scheme.lower()

    # Public suffix and domain extraction (offline only)
    ext = offline_extractor(normalized)
    domain = ext.domain.lower()
    suffix = ext.suffix.lower()
    subdomain = ext.subdomain.lower()

    subdomain_parts = [p for p in subdomain.split(".") if p]
    subdomain_count = len(subdomain_parts)
    registered_domain = f"{domain}.{suffix}" if suffix else domain

    # IP host analysis (IPv4, IPv6, localhost, private, cloud metadata)
    is_ip_host, is_ipv4, is_ipv6, is_priv = inspect_ip_host(host)

    # URL Shortener detection
    is_shortener = registered_domain in SHORTENER_DOMAINS

    # Suspicious TLD check
    has_suspicious_tld = (suffix in SUSPICIOUS_TLDS) or any(
        s in SUSPICIOUS_TLDS for s in suffix.split(".")
    )

    # Path depth
    path_depth = len([p for p in path.split("/") if p])

    # Punycode and IDN indicators
    is_punycode = "xn--" in host or "xn--" in normalized.lower()
    is_idn = is_punycode or any(ord(c) > 127 for c in raw_url)

    # Shannon Entropy (randomness / DGA detection)
    hostname_entropy = calculate_entropy(host)
    url_entropy = calculate_entropy(normalized)

    # Query parameters
    try:
        query_params = parse_qsl(query, keep_blank_values=True)
        query_param_count = len(query_params)
    except Exception:
        query_param_count = 0

    # Suspicious keywords presence (login, verify, kyc, etc.)
    # Note: These signals must NOT automatically mean malicious
    lower_normalized = normalized.lower()
    found_suspicious_keywords: List[str] = [
        kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_normalized
    ]

    # Brand Domain Mismatch evaluation
    claimed_brand, brand_domain_mismatch = evaluate_brand_mismatch(
        registered_domain=registered_domain,
        domain=domain,
        subdomain=subdomain,
        path=path,
        userinfo=userinfo,
    )

    return {
        # Length features
        "url_length": len(normalized),
        "hostname_length": len(host),
        "registered_domain_length": len(registered_domain),
        "path_length": len(path),
        "query_length": len(query),
        "fragment_length": len(fragment),
        # Character count features
        "dot_count": normalized.count("."),
        "hyphen_count": normalized.count("-"),
        "underscore_count": normalized.count("_"),
        "slash_count": normalized.count("/"),
        "at_count": normalized.count("@"),
        "question_count": normalized.count("?"),
        "equal_count": normalized.count("="),
        "ampersand_count": normalized.count("&"),
        "percent_count": normalized.count("%"),
        "digit_count": sum(c.isdigit() for c in normalized),
        # Structural features
        "subdomain_count": subdomain_count,
        "path_depth": path_depth,
        "scheme": scheme,
        "is_https": scheme == "https",
        # IP indicators
        "is_ip_host": is_ip_host,
        "is_ip_address": is_ip_host,
        "is_ipv4": is_ipv4,
        "is_ipv6": is_ipv6,
        "is_private_or_loopback_ip": is_priv,
        # Obfuscation & deception
        "has_at_deception": has_at_deception,
        "deceptive_userinfo": userinfo if has_at_deception else None,
        "is_punycode": is_punycode,
        "is_idn": is_idn,
        "is_shortener": is_shortener,
        "has_suspicious_tld": has_suspicious_tld,
        "hostname_entropy": hostname_entropy,
        "url_entropy": url_entropy,
        "query_param_count": query_param_count,
        # Semantic & brand features
        "suspicious_keywords_present": found_suspicious_keywords,
        "claimed_brand": claimed_brand,
        "brand_domain_mismatch": brand_domain_mismatch,
        # Components
        "hostname": host,
        "domain": domain,
        "suffix": suffix,
        "subdomain": subdomain,
        "registered_domain": registered_domain,
    }
