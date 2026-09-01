# Web Access & API Troubleshooting Platform

A small support-engineering-flavored diagnostic tool: point it at a URL and
it tells you *why* the request behaved the way it did - DNS resolution,
HTTP status, redirect chain, latency, response headers, and whether the
response looks like a block, rate limit, or bot/CAPTCHA challenge. It can
also compare a direct request against the same request routed through a
proxy you control, which is the basis for spotting region- or IP-specific
access issues.

Built to practice the exact troubleshooting workflow this kind of role
uses day to day: reproducing an access issue, isolating whether it's DNS,
network, application, or anti-bot related, and having structured logs and
a correlation ID to hand off for follow-up.

## What it does

- **DNS check** - resolves the hostname, reports the IPs and resolution time.
- **HTTP/S check** - status code, response headers, latency, and the full
  redirect chain (each hop's URL + status).
- **Direct vs. proxy comparison** - runs the same request with and without
  a proxy and returns both results side by side.
- **Block/challenge classification** - labels the outcome as one of:
  `ok`, `redirect`, `rate_limited`, `blocked_403`, `captcha_challenge`,
  `bot_challenge_cloudflare`, `client_error`, `server_error`, `timeout`,
  `connection_error`, `proxy_error`, `dns_failure`, `unknown_error`.
- **Structured JSON logging** - every request attempt is logged with a
  correlation ID, target, mode, latency, and classification, to both
  stdout and `logs/diagnostics.log`.
- **Request history** - every diagnosis is persisted (SQLite) and
  retrievable by correlation ID, similar to looking up a past ticket.
- **REST API + CLI** - the same underlying logic is exposed as a FastAPI
  service and a CLI tool.

### What it deliberately does *not* do

It detects CAPTCHA/bot-challenge responses (recaptcha/hCaptcha markers,
Cloudflare challenge pages, etc.) so you know *that* a request got
challenged. It does not attempt to solve or bypass a CAPTCHA - that's out
of scope and not something this kind of tool should do.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Optional: copy `proxies.example.yaml` to `proxies.yaml` and point it at
proxy nodes you actually control (see `INFRA_SETUP.md` for a quick guide
to standing up your own on cheap/free cloud VMs). Without this file, the
tool still works in direct-only mode.

## Running the API

```bash
uvicorn app.main:app --reload
```

Then either:
- Import `postman/web-diagnostics.postman_collection.json` into Postman, or
- Run `examples/curl_examples.sh`, or
- Hit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/get", "proxy": "eu-west"}'
```

## Running the CLI

```bash
python cli.py diagnose https://httpbin.org/get
python cli.py diagnose https://httpbin.org/get --proxy eu-west --json
python cli.py list-proxies
python cli.py history --limit 10
```

## Tests

```bash
pytest
```

Tests cover the classification logic (pure functions, no network calls) -
the deterministic core of the tool.

## Concepts this project is built around

- **Proxies** - routing a request through an intermediary IP. Useful for
  checking whether an access issue is specific to your own IP/region.
  Residential/mobile proxies look more like real end-user traffic than
  datacenter proxies, which is why datacenter IPs get blocked more often.
- **Bot detection / CAPTCHA challenges** - sites use signals like
  request headers, TLS/JA3 fingerprints, rate of requests, and
  JS-execution checks to decide whether traffic looks automated. A
  CAPTCHA or a Cloudflare "checking your browser" page is usually the
  visible result of that decision, not the detection itself.
- **Redirect chains** - a single URL can hop through several redirects
  before landing on a final response; each hop can fail independently
  (auth redirect loop, expired link, geo-redirect).
- **Rate limiting (429) vs. blocking (403)** - both look like "it didn't
  work" but imply different fixes: back off and retry vs. the IP/pattern
  is flagged entirely.

## Project layout

```
app/
  main.py            FastAPI app (REST endpoints)
  diagnostics.py      DNS + HTTP request orchestration
  classification.py   Block/CAPTCHA/rate-limit classification heuristics
  proxies.py           Proxy config loading
  history.py           SQLite-backed run history
  logging_config.py    Structured JSON logging
  models.py            Pydantic request/response models
cli.py                 CLI entrypoint
postman/               Postman collection
examples/              cURL examples
tests/                 Unit tests for classification logic
```
