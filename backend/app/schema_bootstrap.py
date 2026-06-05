from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_runtime_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "items" in inspector.get_table_names():
        _add_column(engine, "items", "pool_id", "INTEGER")
    if "monitor_pools" in inspector.get_table_names():
        _add_column(engine, "monitor_pools", "last_collected_at", "TIMESTAMP")


def _add_column(engine: Engine, table: str, column: str, definition: str) -> None:
    inspector = inspect(engine)
    columns = {row["name"] for row in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
