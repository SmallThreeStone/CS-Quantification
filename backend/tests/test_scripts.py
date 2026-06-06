from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_backup_postgres_script_uses_compose_dump_and_retention():
    script = (ROOT / "scripts" / "backup_postgres.ps1").read_text(encoding="utf-8")

    assert "docker compose -f $ComposeFile exec -T postgres pg_dump" in script
    assert "-F c" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script
    assert "Remove-Item -Force" in script


def test_backup_config_script_archives_env_compose_and_scripts():
    script = (ROOT / "scripts" / "backup_config.ps1").read_text(encoding="utf-8")

    assert '".env"' in script
    assert '"docker-compose.yml"' in script
    assert '"CLAUDE.md"' in script
    assert 'Test-Path -LiteralPath "scripts"' in script
    assert "Compress-Archive" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script
