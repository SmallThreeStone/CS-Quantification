#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(pwd)"
CRON_FILE="/etc/cron.d/cs-quant-backup"
RUN_USER="${SUDO_USER:-$(id -un)}"
POSTGRES_HOUR="3"
POSTGRES_MINUTE="10"
CONFIG_HOUR="3"
CONFIG_MINUTE="40"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --cron-file)
      CRON_FILE="$2"
      shift 2
      ;;
    --user)
      RUN_USER="$2"
      shift 2
      ;;
    --postgres-time)
      POSTGRES_HOUR="${2%%:*}"
      POSTGRES_MINUTE="${2##*:}"
      shift 2
      ;;
    --config-time)
      CONFIG_HOUR="${2%%:*}"
      CONFIG_MINUTE="${2##*:}"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$(id -u)" -ne 0 ] && [[ "$CRON_FILE" == /etc/cron.d/* ]]; then
  echo "installing to /etc/cron.d requires root; rerun with sudo" >&2
  exit 1
fi

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
mkdir -p "$PROJECT_DIR/backups/logs"

cat > "$CRON_FILE" <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

${POSTGRES_MINUTE} ${POSTGRES_HOUR} * * * ${RUN_USER} cd ${PROJECT_DIR} && bash scripts/backup_postgres.sh >> backups/logs/postgres_backup.log 2>&1
${CONFIG_MINUTE} ${CONFIG_HOUR} * * * ${RUN_USER} cd ${PROJECT_DIR} && bash scripts/backup_config.sh >> backups/logs/config_backup.log 2>&1
EOF

chmod 0644 "$CRON_FILE"

echo "== backup cron installed =="
echo "file=${CRON_FILE}"
echo "user=${RUN_USER}"
echo "project=${PROJECT_DIR}"
echo "postgres=${POSTGRES_HOUR}:${POSTGRES_MINUTE}"
echo "config=${CONFIG_HOUR}:${CONFIG_MINUTE}"
