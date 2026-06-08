#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ ! -f "$ENV_FILE" ]; then
  echo "FAIL env file not found: $ENV_FILE" >&2
  exit 1
fi

get_env() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
  line="${line#*=}"
  line="${line%\"}"
  line="${line#\"}"
  line="${line%\'}"
  line="${line#\'}"
  printf "%s" "$line"
}

FAILED=false

fail() {
  echo "FAIL $1"
  FAILED=true
}

warn() {
  echo "WARN $1"
}

ok() {
  echo "OK $1"
}

POSTGRES_PASSWORD="$(get_env POSTGRES_PASSWORD)"
CORS_ORIGINS="$(get_env CORS_ORIGINS)"
MARKET_PROVIDER="$(get_env MARKET_PROVIDER)"
STEAM_ORDERBOOK_ENABLED="$(get_env STEAM_ORDERBOOK_ENABLED)"
WORKER_SLEEP_SECONDS="$(get_env WORKER_SLEEP_SECONDS)"
PUSH_CHANNEL="$(get_env PUSH_CHANNEL)"
WECHAT_WEBHOOK_URL="$(get_env WECHAT_WEBHOOK_URL)"
QQ_WEBHOOK_URL="$(get_env QQ_WEBHOOK_URL)"

echo "== env check =="
echo "file=${ENV_FILE}"

if [ -z "$POSTGRES_PASSWORD" ]; then
  fail "POSTGRES_PASSWORD is empty"
elif [ "$POSTGRES_PASSWORD" = "change_me" ] || [ "$POSTGRES_PASSWORD" = "replace_with_strong_password" ] || [ "$POSTGRES_PASSWORD" = "cs_quant_password" ]; then
  fail "POSTGRES_PASSWORD still uses a placeholder or default value"
elif [ "${#POSTGRES_PASSWORD}" -lt 16 ]; then
  fail "POSTGRES_PASSWORD should be at least 16 characters"
else
  ok "POSTGRES_PASSWORD is set"
fi

if [ "$MARKET_PROVIDER" != "steam" ]; then
  fail "MARKET_PROVIDER should be steam for cloud P0 validation"
else
  ok "MARKET_PROVIDER=steam"
fi

if [ "$STEAM_ORDERBOOK_ENABLED" != "true" ]; then
  warn "STEAM_ORDERBOOK_ENABLED is not true; buy/sell depth may be incomplete"
else
  ok "STEAM_ORDERBOOK_ENABLED=true"
fi

if [ -z "$CORS_ORIGINS" ]; then
  fail "CORS_ORIGINS is empty"
elif echo "$CORS_ORIGINS" | grep -Eq "your-server-ip|your-domain|localhost|127\.0\.0\.1"; then
  fail "CORS_ORIGINS still contains local or placeholder origins"
else
  ok "CORS_ORIGINS is production-like"
fi

if ! echo "$WORKER_SLEEP_SECONDS" | grep -Eq "^[0-9]+$"; then
  fail "WORKER_SLEEP_SECONDS must be an integer"
elif [ "$WORKER_SLEEP_SECONDS" -lt 10 ]; then
  warn "WORKER_SLEEP_SECONDS is below 10; watch Steam rate limits"
else
  ok "WORKER_SLEEP_SECONDS=${WORKER_SLEEP_SECONDS}"
fi

case "$PUSH_CHANNEL" in
  wechat)
    if [ -z "$WECHAT_WEBHOOK_URL" ]; then
      fail "PUSH_CHANNEL=wechat but WECHAT_WEBHOOK_URL is empty"
    else
      ok "wechat webhook is configured"
    fi
    ;;
  qq)
    if [ -z "$QQ_WEBHOOK_URL" ]; then
      fail "PUSH_CHANNEL=qq but QQ_WEBHOOK_URL is empty"
    else
      ok "qq webhook is configured"
    fi
    ;;
  none|"")
    fail "PUSH_CHANNEL should be wechat or qq for cloud deployment"
    ;;
  *)
    fail "PUSH_CHANNEL must be wechat, qq, or none"
    ;;
esac

if [ "$FAILED" = true ]; then
  exit 1
fi

echo "env check passed"
