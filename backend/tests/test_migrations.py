from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app import models
from app.config import settings
from app.database import Base
from app.migration_runner import run_migrations


def test_alembic_upgrade_creates_core_tables(tmp_path):
    db_path = tmp_path / "migration.db"
    previous_url = settings.database_url
    settings.database_url = f"sqlite:///{db_path}"
    try:
        backend_dir = Path(__file__).resolve().parents[1]
        config = Config(str(backend_dir / "alembic.ini"))
        config.set_main_option("script_location", str(backend_dir / "migrations"))

        command.upgrade(config, "head")

        engine = create_engine(settings.database_url)
        tables = set(inspect(engine).get_table_names())
        assert {"items", "market_snapshots", "alerts", "strategy_configs", "alembic_version"} <= tables
    finally:
        settings.database_url = previous_url


def test_migration_runner_stamps_existing_schema(tmp_path):
    db_path = tmp_path / "existing.db"
    previous_url = settings.database_url
    settings.database_url = f"sqlite:///{db_path}"
    try:
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)

        run_migrations()

        tables = set(inspect(engine).get_table_names())
        assert "alembic_version" in tables
    finally:
        settings.database_url = previous_url
