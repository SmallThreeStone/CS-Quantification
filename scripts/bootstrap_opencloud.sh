#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/data/cs-market-monitor"
INSTALL_DOCKER=true

while [ "$#" -gt 0 ]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --skip-docker)
      INSTALL_DOCKER=false
      shift
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "bootstrapping OpenCloud OS 9 requires root; rerun with sudo" >&2
  exit 1
fi

if ! command -v dnf >/dev/null 2>&1; then
  echo "dnf not found; this script is intended for OpenCloud OS 9" >&2
  exit 2
fi

dnf -y install dnf-plugins-core ca-certificates curl git zip unzip tar gzip cronie firewalld iproute

if [ "$INSTALL_DOCKER" = true ]; then
  if ! dnf repolist all | grep -q "docker-ce"; then
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  fi
  dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi

systemctl enable --now firewalld
systemctl enable --now crond

mkdir -p "$PROJECT_DIR"

if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ] && command -v usermod >/dev/null 2>&1; then
  usermod -aG docker "$SUDO_USER" || true
fi

echo "== OpenCloud OS 9 bootstrap complete =="
echo "project_dir=${PROJECT_DIR}"
echo "docker=$(docker --version 2>/dev/null || echo skipped)"
echo "compose=$(docker compose version 2>/dev/null || echo skipped)"
echo "firewalld=$(systemctl is-active firewalld)"
echo "crond=$(systemctl is-active crond)"
echo "next=git clone git@github.com:SmallThreeStone/CS-Quantification.git ${PROJECT_DIR}"
echo "next=cp .env.production.example .env"
echo "next=sudo bash scripts/configure_firewall.sh --ssh-port 22"
