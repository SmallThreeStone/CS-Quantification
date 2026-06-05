"""strategy price volatility

Revision ID: 20260605_0006
Revises: 20260605_0005
Create Date: 2026-06-05 00:00:05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0006"
down_revision = "20260605_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "strategy_configs",
        sa.Column("min_price_volatility_rate", sa.Float(), nullable=False, server_default="0.08"),
    )


def downgrade() -> None:
    op.drop_column("strategy_configs", "min_price_volatility_rate")
