from pathlib import Path

import yaml

from app.models import ProxyConfig

ROOT = Path(__file__).resolve().parent.parent
PROXIES_FILE = ROOT / "proxies.yaml"
PROXIES_EXAMPLE_FILE = ROOT / "proxies.example.yaml"


def load_proxies() -> list[ProxyConfig]:
    path = PROXIES_FILE if PROXIES_FILE.exists() else None
    if path is None:
        return []

    data = yaml.safe_load(path.read_text()) or {}
    return [ProxyConfig(**entry) for entry in data.get("proxies", [])]


def get_proxy(label: str) -> ProxyConfig | None:
    for proxy in load_proxies():
        if proxy.label == label:
            return proxy
    return None
