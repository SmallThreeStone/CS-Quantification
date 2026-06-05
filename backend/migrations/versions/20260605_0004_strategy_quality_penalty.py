"""strategy quality penalty

Revision ID: 20260605_0004
Revises: 20260605_0003
Create Date: 2026-06-05 00:00:03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0004"
down_revision = "20260605_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "strategy_configs",
        sa.Column("quality_penalty_max", sa.Integer(), nullable=False, server_default="30"),
    )


def downgrade() -> None:
    op.drop_column("strategy_configs", "quality_penalty_max")
