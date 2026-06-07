#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="./backups/postgres"
RETENTION_DAYS="14"
COMPOSE_FILE="docker-compose.yml"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --retention-days)
      RETENTION_DAYS="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

env_value() {
  local name="$1"
  local default_value="$2"
  if [ -f ".env" ]; then
    local line
    line="$(grep -E "^${name}=" .env | head -n 1 || true)"
    if [ -n "$line" ]; then
      echo "${line#*=}"
      return
    fi
  fi
  echo "$default_value"
}

DB_NAME="$(env_value POSTGRES_DB cs_quant)"
DB_USER="$(env_value POSTGRES_USER cs_quant)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
CONTAINER_PATH="/tmp/${DB_NAME}_${TIMESTAMP}.dump"

echo "== backup postgres =="
echo "database=${DB_NAME} user=${DB_USER} output=${BACKUP_PATH}"

docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f "$CONTAINER_PATH"
docker compose -f "$COMPOSE_FILE" cp "postgres:${CONTAINER_PATH}" "$BACKUP_PATH"
docker compose -f "$COMPOSE_FILE" exec -T postgres rm "$CONTAINER_PATH"

if [ ! -s "$BACKUP_PATH" ]; then
  echo "backup file is empty: $BACKUP_PATH" >&2
  exit 1
fi

if [ "$RETENTION_DAYS" -gt 0 ]; then
  find "$BACKUP_DIR" -type f -name "*.dump" -mtime "+$RETENTION_DAYS" -delete
fi

echo "== backup complete =="
echo "path=${BACKUP_PATH}"
echo "size=$(wc -c < "$BACKUP_PATH")"
