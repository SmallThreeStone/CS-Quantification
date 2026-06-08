#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost"
COLLECT=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --collect)
      COLLECT=true
      shift
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

json_get() {
  local label="$1"
  local path="$2"
  echo "== ${label} =="
  curl -fsS "${BASE_URL}${path}" | python3 -m json.tool
}

json_post() {
  local label="$1"
  local path="$2"
  echo "== ${label} =="
  curl -fsS -X POST "${BASE_URL}${path}" | python3 -m json.tool
}

echo "== docker compose ps =="
docker compose ps

echo "== env =="
bash scripts/check_env.sh

echo "== firewall =="
bash scripts/check_firewall.sh

json_get "health" "/api/health"
json_get "ops-health" "/api/ops/health"
json_get "api-latency" "/api/ops/api-latency"
json_get "db-write-volume" "/api/ops/db-write-volume"
json_get "host-resources" "/api/ops/host-resources"
json_get "backups" "/api/ops/backups"
json_get "ops-readiness" "/api/ops/readiness"
json_get "ops-runtime" "/api/ops/runtime"
json_get "runtime-audit" "/api/ops/runtime-audit"
json_get "acceptance" "/api/ops/acceptance"
json_get "mvp-scope" "/api/ops/mvp-scope"
json_get "p0-summary" "/api/ops/p0-summary"
json_get "source-config" "/api/source/config"
json_get "alert-coverage" "/api/alerts/coverage"
json_get "monitor" "/api/monitor"
json_get "monitor-coverage" "/api/monitor/coverage"
json_get "steam-nameid-todo" "/api/steam-nameids/todo"
json_get "collect-runs" "/api/collect-runs"

if [ "$COLLECT" = true ]; then
  json_post "collect" "/api/collect"
  json_get "collect-runs-after" "/api/collect-runs"
fi

echo "== frontend =="
curl -fsS -o /dev/null -w "status=%{http_code}\n" "$BASE_URL"
