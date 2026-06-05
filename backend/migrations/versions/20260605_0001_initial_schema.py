"""initial schema

Revision ID: 20260605_0001
Revises: 
Create Date: 2026-06-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitor_pools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platforms_code"), "platforms", ["code"], unique=True)
    op.create_table(
        "strategy_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("min_absolute_sell_change", sa.Integer(), nullable=False),
        sa.Column("min_sell_change_rate", sa.Float(), nullable=False),
        sa.Column("min_price_change_rate", sa.Float(), nullable=False),
        sa.Column("min_buy_change_rate", sa.Float(), nullable=False),
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "collect_run_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("snapshot_count", sa.Integer(), nullable=False),
        sa.Column("alert_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_collect_run_logs_mode"), "collect_run_logs", ["mode"], unique=False)
    op.create_index(op.f("ix_collect_run_logs_started_at"), "collect_run_logs", ["started_at"], unique=False)
    op.create_index(op.f("ix_collect_run_logs_status"), "collect_run_logs", ["status"], unique=False)
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("market_hash_name", sa.String(length=240), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("exterior", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("pool_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["pool_id"], ["monitor_pools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_market_hash_name"), "items", ["market_hash_name"], unique=True)
    op.create_index(op.f("ix_items_pool_id"), "items", ["pool_id"], unique=False)
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("lowest_price", sa.Float(), nullable=False),
        sa.Column("sell_count", sa.Integer(), nullable=False),
        sa.Column("highest_buy_price", sa.Float(), nullable=False),
        sa.Column("buy_count", sa.Integer(), nullable=False),
        sa.Column("volume_24h", sa.Integer(), nullable=False),
        sa.Column("avg_price_24h", sa.Float(), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_snapshots_captured_at"), "market_snapshots", ["captured_at"], unique=False)
    op.create_index(op.f("ix_market_snapshots_item_id"), "market_snapshots", ["item_id"], unique=False)
    op.create_index(op.f("ix_market_snapshots_platform_id"), "market_snapshots", ["platform_id"], unique=False)
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("previous_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("absolute_change", sa.Float(), nullable=False),
        sa.Column("change_rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["market_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)
    op.create_index(op.f("ix_alerts_item_id"), "alerts", ["item_id"], unique=False)
    op.create_index(op.f("ix_alerts_platform_id"), "alerts", ["platform_id"], unique=False)
    op.create_index(op.f("ix_alerts_snapshot_id"), "alerts", ["snapshot_id"], unique=False)
    op.create_table(
        "backtest_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("horizon_minutes", sa.Integer(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=False),
        sa.Column("price_change", sa.Float(), nullable=False),
        sa.Column("change_rate", sa.Float(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_results_alert_id"), "backtest_results", ["alert_id"], unique=False)
    op.create_index(op.f("ix_backtest_results_created_at"), "backtest_results", ["created_at"], unique=False)
    op.create_index(op.f("ix_backtest_results_evaluated_at"), "backtest_results", ["evaluated_at"], unique=False)
    op.create_index(op.f("ix_backtest_results_horizon_minutes"), "backtest_results", ["horizon_minutes"], unique=False)
    op.create_index(op.f("ix_backtest_results_item_id"), "backtest_results", ["item_id"], unique=False)
    op.create_index(op.f("ix_backtest_results_platform_id"), "backtest_results", ["platform_id"], unique=False)
    op.create_table(
        "push_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("target", sa.String(length=240), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_push_records_alert_id"), "push_records", ["alert_id"], unique=False)
    op.create_index(op.f("ix_push_records_channel"), "push_records", ["channel"], unique=False)
    op.create_index(op.f("ix_push_records_created_at"), "push_records", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_push_records_created_at"), table_name="push_records")
    op.drop_index(op.f("ix_push_records_channel"), table_name="push_records")
    op.drop_index(op.f("ix_push_records_alert_id"), table_name="push_records")
    op.drop_table("push_records")
    op.drop_index(op.f("ix_backtest_results_platform_id"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_item_id"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_horizon_minutes"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_evaluated_at"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_created_at"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_alert_id"), table_name="backtest_results")
    op.drop_table("backtest_results")
    op.drop_index(op.f("ix_alerts_snapshot_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_platform_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_item_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_alert_type"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_market_snapshots_platform_id"), table_name="market_snapshots")
    op.drop_index(op.f("ix_market_snapshots_item_id"), table_name="market_snapshots")
    op.drop_index(op.f("ix_market_snapshots_captured_at"), table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_index(op.f("ix_items_pool_id"), table_name="items")
    op.drop_index(op.f("ix_items_market_hash_name"), table_name="items")
    op.drop_table("items")
    op.drop_index(op.f("ix_collect_run_logs_status"), table_name="collect_run_logs")
    op.drop_index(op.f("ix_collect_run_logs_started_at"), table_name="collect_run_logs")
    op.drop_index(op.f("ix_collect_run_logs_mode"), table_name="collect_run_logs")
    op.drop_table("collect_run_logs")
    op.drop_table("strategy_configs")
    op.drop_index(op.f("ix_platforms_code"), table_name="platforms")
    op.drop_table("platforms")
    op.drop_table("monitor_pools")
