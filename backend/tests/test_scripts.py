from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_backup_postgres_script_uses_compose_dump_and_retention():
    script = (ROOT / "scripts" / "backup_postgres.ps1").read_text(encoding="utf-8")

    assert "docker compose -f $ComposeFile exec -T postgres pg_dump" in script
    assert "-F c" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script
    assert "Remove-Item -Force" in script
