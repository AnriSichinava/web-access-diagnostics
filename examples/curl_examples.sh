#!/usr/bin/env bash
# Example cURL calls against the local diagnostics API.
# Start the server first: uvicorn app.main:app --reload

set -e
BASE_URL="http://127.0.0.1:8000"

echo "== health =="
curl -s "$BASE_URL/health" | jq .

echo "== list configured proxies =="
curl -s "$BASE_URL/proxies" | jq .

echo "== diagnose a target URL (direct only) =="
curl -s -X POST "$BASE_URL/diagnose" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/get"}' | jq .

echo "== diagnose with a proxy comparison =="
curl -s -X POST "$BASE_URL/diagnose" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/get", "proxy": "eu-west"}' | jq .

echo "== recent history =="
curl -s "$BASE_URL/history?limit=10" | jq .
