from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ProxyConfig(BaseModel):
    label: str
    host: str
    port: int
    scheme: str = "http"
    region: str = "unknown"

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


class DnsResult(BaseModel):
    hostname: str
    resolved_ips: list[str] = Field(default_factory=list)
    resolution_time_ms: float
    error: Optional[str] = None


class RedirectHop(BaseModel):
    url: str
    status_code: int


class AttemptResult(BaseModel):
    mode: str  # "direct" | "proxy"
    proxy_label: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: float
    headers: dict[str, str] = Field(default_factory=dict)
    redirect_chain: list[RedirectHop] = Field(default_factory=list)
    response_snippet: Optional[str] = None
    error: Optional[str] = None
    classification: str


class DiagnosisReport(BaseModel):
    correlation_id: str
    target_url: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dns: DnsResult
    direct: AttemptResult
    proxy: Optional[AttemptResult] = None


class DiagnoseRequest(BaseModel):
    url: str
    proxy: Optional[str] = None
    compare: bool = True
    follow_redirects: bool = True
