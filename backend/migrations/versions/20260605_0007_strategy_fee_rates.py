"""strategy fee rates

Revision ID: 20260605_0007
Revises: 20260605_0006
Create Date: 2026-06-05 00:00:06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0007"
down_revision = "20260605_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("strategy_configs", sa.Column("sell_fee_rate", sa.Float(), nullable=False, server_default="0.13"))
    op.add_column("strategy_configs", sa.Column("withdraw_fee_rate", sa.Float(), nullable=False, server_default="0"))
    op.add_column("strategy_configs", sa.Column("fx_rate", sa.Float(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("strategy_configs", "fx_rate")
    op.drop_column("strategy_configs", "withdraw_fee_rate")
    op.drop_column("strategy_configs", "sell_fee_rate")
