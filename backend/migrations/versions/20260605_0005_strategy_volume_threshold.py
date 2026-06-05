"""strategy volume threshold

Revision ID: 20260605_0005
Revises: 20260605_0004
Create Date: 2026-06-05 00:00:04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0005"
down_revision = "20260605_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "strategy_configs",
        sa.Column("min_volume_change_rate", sa.Float(), nullable=False, server_default="0.5"),
    )


def downgrade() -> None:
    op.drop_column("strategy_configs", "min_volume_change_rate")
