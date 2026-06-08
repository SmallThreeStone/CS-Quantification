#!/usr/bin/env bash
set -euo pipefail

if ! command -v ss >/dev/null 2>&1; then
  echo "ss command not found; install iproute package first" >&2
  exit 2
fi

LISTENING="$(ss -ltn)"
FAILED=false

check_loopback_only() {
  local port="$1"
  local label="$2"
  local rows
  rows="$(echo "$LISTENING" | awk -v port=":${port}$" '$4 ~ port { print $4 }')"
  if [ -z "$rows" ]; then
    echo "WARN ${label} port ${port} is not listening"
    return
  fi
  if echo "$rows" | grep -Ev '^(127\.0\.0\.1|\[::1\]):' >/dev/null; then
    echo "FAIL ${label} port ${port} is exposed beyond loopback:"
    echo "$rows"
    FAILED=true
    return
  fi
  echo "OK ${label} port ${port} is loopback-only"
}

check_public_entry() {
  local port="$1"
  local label="$2"
  if echo "$LISTENING" | awk -v port=":${port}$" '$4 ~ port { found=1 } END { exit found ? 0 : 1 }'; then
    echo "OK ${label} port ${port} is listening"
  else
    echo "WARN ${label} port ${port} is not listening"
  fi
}

check_loopback_only 5432 PostgreSQL
check_loopback_only 6379 Redis
check_loopback_only 8000 Backend
check_public_entry 3139 Frontend

if [ "$FAILED" = true ]; then
  exit 1
fi
