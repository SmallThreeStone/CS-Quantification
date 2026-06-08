#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="./backups/config"
RETENTION_DAYS="30"

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
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
STAGING_DIR="${BACKUP_DIR}/config_${TIMESTAMP}"
ARCHIVE_PATH="${BACKUP_DIR}/config_${TIMESTAMP}.zip"
mkdir -p "$STAGING_DIR"

for file in ".env" ".env.example" ".env.production.example" "docker-compose.yml" "README.md" "CLAUDE.md"; do
  if [ -f "$file" ]; then
    cp "$file" "$STAGING_DIR/"
  else
    echo "skip missing file: $file"
  fi
done

if [ -d "scripts" ]; then
  cp -R "scripts" "$STAGING_DIR/scripts"
fi

(cd "$STAGING_DIR" && zip -qr "../$(basename "$ARCHIVE_PATH")" .)
rm -rf "$STAGING_DIR"

if [ ! -s "$ARCHIVE_PATH" ]; then
  echo "config backup file is empty: $ARCHIVE_PATH" >&2
  exit 1
fi

if [ "$RETENTION_DAYS" -gt 0 ]; then
  find "$BACKUP_DIR" -type f -name "*.zip" -mtime "+$RETENTION_DAYS" -delete
fi

echo "== config backup complete =="
echo "path=${ARCHIVE_PATH}"
echo "size=$(wc -c < "$ARCHIVE_PATH")"
