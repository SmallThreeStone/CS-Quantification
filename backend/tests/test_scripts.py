from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_backup_postgres_script_uses_compose_dump_and_retention():
    script = (ROOT / "scripts" / "backup_postgres.ps1").read_text(encoding="utf-8")

    assert "docker compose -f $ComposeFile exec -T postgres pg_dump" in script
    assert "-F c" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script
    assert "Remove-Item -Force" in script


def test_backup_postgres_shell_script_uses_compose_dump_and_retention():
    script = (ROOT / "scripts" / "backup_postgres.sh").read_text(encoding="utf-8")

    assert 'docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump' in script
    assert "-F c" in script
    assert '[ ! -s "$BACKUP_PATH" ]' in script
    assert "RETENTION_DAYS" in script
    assert 'find "$BACKUP_DIR" -type f -name "*.dump"' in script


def test_backup_config_script_archives_env_compose_and_scripts():
    script = (ROOT / "scripts" / "backup_config.ps1").read_text(encoding="utf-8")

    assert '".env"' in script
    assert '"docker-compose.yml"' in script
    assert '"CLAUDE.md"' in script
    assert 'Test-Path -LiteralPath "scripts"' in script
    assert "Compress-Archive" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script


def test_backup_config_shell_script_archives_env_compose_and_scripts():
    script = (ROOT / "scripts" / "backup_config.sh").read_text(encoding="utf-8")

    assert '".env"' in script
    assert '"docker-compose.yml"' in script
    assert '"CLAUDE.md"' in script
    assert '[ -d "scripts" ]' in script
    assert "zip -qr" in script
    assert '[ ! -s "$ARCHIVE_PATH" ]' in script
    assert "RETENTION_DAYS" in script


def test_verify_deploy_shell_script_checks_core_endpoints_and_collect():
    script = (ROOT / "scripts" / "verify_deploy.sh").read_text(encoding="utf-8")

    assert "docker compose ps" in script
    assert 'json_get "health" "/api/health"' in script
    assert 'json_get "ops-health" "/api/ops/health"' in script
    assert 'json_get "api-latency" "/api/ops/api-latency"' in script
    assert 'json_get "db-write-volume" "/api/ops/db-write-volume"' in script
    assert 'json_get "host-resources" "/api/ops/host-resources"' in script
    assert 'json_get "backups" "/api/ops/backups"' in script
    assert 'json_get "acceptance" "/api/ops/acceptance"' in script
    assert 'json_post "collect" "/api/collect"' in script
    assert 'curl -fsS -o /dev/null -w "status=%{http_code}\\n" "$BASE_URL"' in script
