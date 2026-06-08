from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_compose_binds_internal_services_to_loopback_only():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "127.0.0.1:5432:5432" in compose
    assert "127.0.0.1:6379:6379" in compose
    assert "127.0.0.1:8000:8000" in compose
    assert "3139:80" in compose
    assert '"5432:5432"' not in compose
    assert '"6379:6379"' not in compose
    assert '"8000:8000"' not in compose


def test_compose_passes_build_mirror_args():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "PIP_INDEX_URL" in compose
    assert "PIP_DEFAULT_TIMEOUT" in compose
    assert "NPM_REGISTRY" in compose


def test_dockerfiles_support_build_mirrors():
    backend = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    frontend = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")

    assert "ARG PIP_INDEX_URL" in backend
    assert "ARG PIP_DEFAULT_TIMEOUT" in backend
    assert "ENV PIP_INDEX_URL" in backend
    assert "ENV PIP_DEFAULT_TIMEOUT" in backend
    assert "ARG NPM_REGISTRY" in frontend
    assert 'npm config set registry "$NPM_REGISTRY"' in frontend


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
    assert '".env.production.example"' in script
    assert '"CLAUDE.md"' in script
    assert 'Test-Path -LiteralPath "scripts"' in script
    assert "Compress-Archive" in script
    assert "if ($file.Length -le 0)" in script
    assert "RetentionDays" in script


def test_backup_config_shell_script_archives_env_compose_and_scripts():
    script = (ROOT / "scripts" / "backup_config.sh").read_text(encoding="utf-8")

    assert '".env"' in script
    assert '"docker-compose.yml"' in script
    assert '".env.production.example"' in script
    assert '"CLAUDE.md"' in script
    assert '[ -d "scripts" ]' in script
    assert "zip -qr" in script
    assert '[ ! -s "$ARCHIVE_PATH" ]' in script
    assert "RETENTION_DAYS" in script


def test_verify_deploy_shell_script_checks_core_endpoints_and_collect():
    script = (ROOT / "scripts" / "verify_deploy.sh").read_text(encoding="utf-8")

    assert "docker compose ps" in script
    assert "bash scripts/check_env.sh" in script
    assert "bash scripts/check_firewall.sh" in script
    assert 'json_get "health" "/api/health"' in script
    assert 'json_get "ops-health" "/api/ops/health"' in script
    assert 'json_get "api-latency" "/api/ops/api-latency"' in script
    assert 'json_get "db-write-volume" "/api/ops/db-write-volume"' in script
    assert 'json_get "host-resources" "/api/ops/host-resources"' in script
    assert 'json_get "backups" "/api/ops/backups"' in script
    assert 'json_get "acceptance" "/api/ops/acceptance"' in script
    assert 'json_post "collect" "/api/collect"' in script
    assert 'curl -fsS -o /dev/null -w "status=%{http_code}\\n" "$BASE_URL"' in script


def test_check_firewall_shell_script_guards_internal_ports():
    script = (ROOT / "scripts" / "check_firewall.sh").read_text(encoding="utf-8")

    assert "ss -ltn" in script
    assert "check_loopback_only 5432 PostgreSQL" in script
    assert "check_loopback_only 6379 Redis" in script
    assert "check_loopback_only 8000 Backend" in script
    assert "check_public_entry 3139 Frontend" in script
    assert "exposed beyond loopback" in script


def test_check_env_shell_script_guards_cloud_env_values():
    script = (ROOT / "scripts" / "check_env.sh").read_text(encoding="utf-8")

    assert 'ENV_FILE=".env"' in script
    assert "--env-file" in script
    assert "POSTGRES_PASSWORD still uses a placeholder or default value" in script
    assert "POSTGRES_PASSWORD should be at least 16 characters" in script
    assert "MARKET_PROVIDER should be steam for cloud P0 validation" in script
    assert "STEAM_ORDERBOOK_ENABLED is not true" in script
    assert "CORS_ORIGINS still contains local or placeholder origins" in script
    assert "WORKER_SLEEP_SECONDS must be an integer" in script
    assert "PUSH_CHANNEL=wechat but WECHAT_WEBHOOK_URL is empty" in script
    assert "PUSH_CHANNEL=qq but QQ_WEBHOOK_URL is empty" in script
    assert "PUSH_CHANNEL should be wechat or qq for cloud deployment" in script


def test_check_update_ready_shell_script_guards_git_update_state():
    script = (ROOT / "scripts" / "check_update_ready.sh").read_text(encoding="utf-8")

    assert 'REMOTE="origin"' in script
    assert 'BRANCH="feature/initial-mvp"' in script
    assert "--target-commit" in script
    assert "git rev-parse --is-inside-work-tree" in script
    assert "git status --porcelain" in script
    assert 'git fetch "$REMOTE" "$BRANCH"' in script
    assert "git rev-parse FETCH_HEAD" in script
    assert "does not match target commit" in script
    assert "git merge-base --is-ancestor" in script
    assert "git pull --ff-only" in script


def test_configure_firewall_shell_script_allows_only_public_entrypoints():
    script = (ROOT / "scripts" / "configure_firewall.sh").read_text(encoding="utf-8")

    assert "configuring firewalld requires root" in script
    assert "firewall-cmd" in script
    assert "systemctl enable --now firewalld" in script
    assert '--add-port="${SSH_PORT}/tcp"' in script
    assert "--add-port=3139/tcp" in script
    assert "for port in 80 443 5432 6379 8000" in script
    assert '--remove-port="${port}/tcp"' in script
    assert "--remove-service=http" in script
    assert "--remove-service=https" in script
    assert "bash scripts/check_firewall.sh" in script


def test_bootstrap_opencloud_script_installs_runtime_dependencies():
    script = (ROOT / "scripts" / "bootstrap_opencloud.sh").read_text(encoding="utf-8")

    assert "bootstrapping OpenCloud OS 9 requires root" in script
    assert "dnf -y install dnf-plugins-core ca-certificates curl git zip unzip tar gzip cronie firewalld iproute" in script
    assert "https://download.docker.com/linux/centos/docker-ce.repo" in script
    assert "docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" in script
    assert "systemctl enable --now docker" in script
    assert "systemctl enable --now firewalld" in script
    assert "systemctl enable --now crond" in script
    assert "git clone git@github.com:SmallThreeStone/CS-Quantification.git" in script
    assert "cp .env.production.example .env" in script


def test_production_env_template_defaults_to_steam_and_no_secret():
    env_template = (ROOT / ".env.production.example").read_text(encoding="utf-8")

    assert "POSTGRES_PASSWORD=replace_with_strong_password" in env_template
    assert "MARKET_PROVIDER=steam" in env_template
    assert "STEAM_ORDERBOOK_ENABLED=true" in env_template
    assert "PUSH_CHANNEL=wechat" in env_template
    assert "WECHAT_WEBHOOK_URL=" in env_template
    assert "QQ_WEBHOOK_URL=" in env_template
    assert "PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple" in env_template
    assert "PIP_DEFAULT_TIMEOUT=300" in env_template
    assert "NPM_REGISTRY=https://registry.npmmirror.com/" in env_template
    assert "cs_quant_password" not in env_template


def test_install_backup_cron_script_installs_daily_backup_jobs():
    script = (ROOT / "scripts" / "install_backup_cron.sh").read_text(encoding="utf-8")

    assert 'CRON_FILE="/etc/cron.d/cs-quant-backup"' in script
    assert "--project-dir" in script
    assert "--postgres-time" in script
    assert "--config-time" in script
    assert "installing to /etc/cron.d requires root" in script
    assert 'PROJECT_CRON_FILE="$PROJECT_DIR/backups/cron/cs-quant-backup"' in script
    assert 'cp "$PROJECT_CRON_FILE" "$CRON_FILE"' in script
    assert "bash scripts/backup_postgres.sh >> backups/logs/postgres_backup.log 2>&1" in script
    assert "bash scripts/backup_config.sh >> backups/logs/config_backup.log 2>&1" in script
    assert 'chmod 0644 "$CRON_FILE"' in script
