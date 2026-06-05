from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_runtime_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "items" in inspector.get_table_names():
        _add_column(engine, "items", "pool_id", "INTEGER")
        _add_column(engine, "items", "steam_item_nameid", "VARCHAR(80) DEFAULT ''")
    if "monitor_pools" in inspector.get_table_names():
        _add_column(engine, "monitor_pools", "last_collected_at", "TIMESTAMP")
    if "collect_run_logs" in inspector.get_table_names():
        _add_column(engine, "collect_run_logs", "real_field_count", "INTEGER DEFAULT 0")
        _add_column(engine, "collect_run_logs", "fallback_field_count", "INTEGER DEFAULT 0")
        _add_column(engine, "collect_run_logs", "fallback_count", "INTEGER DEFAULT 0")
    if "strategy_configs" in inspector.get_table_names():
        _add_column(engine, "strategy_configs", "quality_penalty_max", "INTEGER DEFAULT 30")
        _add_column(engine, "strategy_configs", "min_volume_change_rate", "FLOAT DEFAULT 0.5")
        _add_column(engine, "strategy_configs", "min_price_volatility_rate", "FLOAT DEFAULT 0.08")


def _add_column(engine: Engine, table: str, column: str, definition: str) -> None:
    inspector = inspect(engine)
    columns = {row["name"] for row in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
