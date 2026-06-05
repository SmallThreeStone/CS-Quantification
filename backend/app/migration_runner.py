from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import settings
from app.schema_bootstrap import ensure_runtime_columns


def run_migrations() -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))

    if {"items", "market_snapshots"} <= tables and "alembic_version" not in tables:
        ensure_runtime_columns(engine)
        command.stamp(config, "head")
    command.upgrade(config, "head")


if __name__ == "__main__":
    run_migrations()
