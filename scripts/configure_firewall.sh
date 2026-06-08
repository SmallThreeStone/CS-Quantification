#!/usr/bin/env bash
set -euo pipefail

ZONE="public"
SSH_PORT="22"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --zone)
      ZONE="$2"
      shift 2
      ;;
    --ssh-port)
      SSH_PORT="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "configuring firewalld requires root; rerun with sudo" >&2
  exit 1
fi

if ! command -v firewall-cmd >/dev/null 2>&1; then
  echo "firewall-cmd not found; install and enable firewalld first" >&2
  exit 2
fi

systemctl enable --now firewalld

firewall-cmd --zone="$ZONE" --permanent --add-port="${SSH_PORT}/tcp"
firewall-cmd --zone="$ZONE" --permanent --add-port=3139/tcp

for port in 80 443 5432 6379 8000; do
  firewall-cmd --zone="$ZONE" --permanent --remove-port="${port}/tcp" >/dev/null 2>&1 || true
done
firewall-cmd --zone="$ZONE" --permanent --remove-service=http >/dev/null 2>&1 || true
firewall-cmd --zone="$ZONE" --permanent --remove-service=https >/dev/null 2>&1 || true

firewall-cmd --reload

echo "== firewalld configured =="
echo "zone=${ZONE}"
echo "ssh=${SSH_PORT}/tcp"
echo "public=3139/tcp"
echo "blocked=80,443,5432,6379,8000"
echo "next=bash scripts/check_firewall.sh"
