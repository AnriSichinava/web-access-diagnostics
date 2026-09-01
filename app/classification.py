"""Heuristics for labeling why a request did or didn't succeed.

Only detects/classifies challenge and block signals - never attempts to
solve or bypass a CAPTCHA/bot-challenge.
"""

CAPTCHA_MARKERS = [
    "g-recaptcha",
    "recaptcha",
    "hcaptcha",
    "h-captcha",
    "cf-turnstile",
    "just a moment",
    "attention required! | cloudflare",
    "challenge-platform",
    "checking your browser",
    "verify you are human",
]

CLOUDFLARE_MARKERS = [
    "cloudflare",
    "cf-mitigated",
    "cf-ray",
]


def classify_response(status_code: int, headers: dict, body: str) -> str:
    body_lower = (body or "").lower()
    header_blob = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()

    if status_code == 503 and any(marker in header_blob or marker in body_lower for marker in CLOUDFLARE_MARKERS):
        return "bot_challenge_cloudflare"

    if any(marker in body_lower for marker in CAPTCHA_MARKERS):
        return "captcha_challenge"

    if status_code == 429:
        return "rate_limited"

    if status_code == 403:
        return "blocked_403"

    if status_code >= 500:
        return "server_error"

    if status_code >= 400:
        return "client_error"

    if 300 <= status_code < 400:
        return "redirect"

    return "ok"


def classify_error(exc: Exception) -> str:
    name = type(exc).__name__.lower()

    if "proxy" in name:
        return "proxy_error"
    if "timeout" in name:
        return "timeout"
    if "connect" in name:
        return "connection_error"
    if "resolv" in name or "nxdomain" in name or "dns" in name:
        return "dns_failure"

    return "unknown_error"
