import time
import uuid
from urllib.parse import urlsplit

import dns.resolver
import httpx

from app.classification import classify_error, classify_response
from app.logging_config import get_logger
from app.models import AttemptResult, DiagnosisReport, DnsResult, ProxyConfig, RedirectHop
from app.proxies import get_proxy

logger = get_logger(__name__)

MAX_REDIRECTS = 10
REQUEST_TIMEOUT = 10.0


def resolve_dns(hostname: str) -> DnsResult:
    start = time.perf_counter()
    try:
        answer = dns.resolver.resolve(hostname, "A", lifetime=5)
        ips = [record.to_text() for record in answer]
        elapsed_ms = (time.perf_counter() - start) * 1000
        return DnsResult(hostname=hostname, resolved_ips=ips, resolution_time_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return DnsResult(hostname=hostname, resolved_ips=[], resolution_time_ms=elapsed_ms, error=str(exc))


def perform_request(
    url: str,
    proxy: ProxyConfig | None,
    follow_redirects: bool,
    mode: str,
    correlation_id: str,
) -> AttemptResult:
    redirect_chain: list[RedirectHop] = []
    start = time.perf_counter()

    try:
        with httpx.Client(follow_redirects=False, timeout=REQUEST_TIMEOUT, proxy=proxy.url if proxy else None) as client:
            current_url = url
            response = None
            for _ in range(MAX_REDIRECTS):
                response = client.get(current_url)
                redirect_chain.append(RedirectHop(url=current_url, status_code=response.status_code))
                if follow_redirects and response.is_redirect:
                    next_url = response.headers.get("location")
                    if not next_url:
                        break
                    current_url = str(httpx.URL(current_url).join(next_url))
                    continue
                break

        latency_ms = (time.perf_counter() - start) * 1000
        body_snippet = response.text[:500]
        classification = classify_response(response.status_code, dict(response.headers), body_snippet)

        logger.info(
            "request completed",
            extra={
                "correlation_id": correlation_id,
                "mode": mode,
                "proxy_label": proxy.label if proxy else None,
                "target_url": url,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 1),
                "classification": classification,
            },
        )

        return AttemptResult(
            mode=mode,
            proxy_label=proxy.label if proxy else None,
            status_code=response.status_code,
            latency_ms=latency_ms,
            headers=dict(response.headers),
            redirect_chain=redirect_chain,
            response_snippet=body_snippet,
            classification=classification,
        )

    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        classification = classify_error(exc)

        logger.info(
            "request failed",
            extra={
                "correlation_id": correlation_id,
                "mode": mode,
                "proxy_label": proxy.label if proxy else None,
                "target_url": url,
                "error": str(exc),
                "latency_ms": round(latency_ms, 1),
                "classification": classification,
            },
        )

        return AttemptResult(
            mode=mode,
            proxy_label=proxy.label if proxy else None,
            latency_ms=latency_ms,
            redirect_chain=redirect_chain,
            error=str(exc),
            classification=classification,
        )


def run_diagnosis(url: str, proxy_label: str | None, follow_redirects: bool = True) -> DiagnosisReport:
    correlation_id = str(uuid.uuid4())
    hostname = urlsplit(url).hostname or url

    logger.info("diagnosis started", extra={"correlation_id": correlation_id, "target_url": url})

    dns_result = resolve_dns(hostname)
    direct_result = perform_request(url, proxy=None, follow_redirects=follow_redirects, mode="direct", correlation_id=correlation_id)

    proxy_result = None
    if proxy_label:
        proxy_cfg = get_proxy(proxy_label)
        if proxy_cfg is None:
            raise ValueError(f"unknown proxy label: {proxy_label}")
        proxy_result = perform_request(url, proxy=proxy_cfg, follow_redirects=follow_redirects, mode="proxy", correlation_id=correlation_id)

    return DiagnosisReport(
        correlation_id=correlation_id,
        target_url=url,
        dns=dns_result,
        direct=direct_result,
        proxy=proxy_result,
    )
