#!/usr/bin/env bash
set -euo pipefail

APP_PORT_VALUE="${APP_PORT:-18080}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${APP_PORT_VALUE}}"
AUTH_CURL_ARGS=()

if [[ "${AUTH_ENABLED:-false}" == "true" && -n "${AUTH_USERNAME:-}" && -n "${AUTH_PASSWORD:-}" ]]; then
  AUTH_CURL_ARGS=(-u "${AUTH_USERNAME}:${AUTH_PASSWORD}")
fi

echo "[1/3] health"
curl -fsS "${BASE_URL}/api/health" >/dev/null

echo "[2/3] sources"
curl -fsS "${AUTH_CURL_ARGS[@]}" "${BASE_URL}/api/sources" >/dev/null

if [[ -n "${SOURCE_ID:-}" && -n "${TOKEN_NAME:-}" ]]; then
  echo "[3/3] summary/details"
  curl -fsS --get \
    "${AUTH_CURL_ARGS[@]}" \
    --data-urlencode "source_id=${SOURCE_ID}" \
    --data-urlencode "token_name=${TOKEN_NAME}" \
    "${BASE_URL}/api/stats/token-cost-summary" >/dev/null
  curl -fsS --get \
    "${AUTH_CURL_ARGS[@]}" \
    --data-urlencode "source_id=${SOURCE_ID}" \
    --data-urlencode "token_name=${TOKEN_NAME}" \
    --data-urlencode "page=1" \
    --data-urlencode "page_size=5" \
    "${BASE_URL}/api/stats/token-cost-details" >/dev/null
else
  echo "[3/3] summary/details skipped"
  echo "Set SOURCE_ID and TOKEN_NAME to enable statistics smoke checks."
fi

echo "Smoke test passed: ${BASE_URL}"
