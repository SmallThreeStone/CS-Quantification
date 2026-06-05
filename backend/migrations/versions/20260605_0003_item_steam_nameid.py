"""item steam nameid

Revision ID: 20260605_0003
Revises: 20260605_0002
Create Date: 2026-06-05 00:00:02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260605_0003"
down_revision = "20260605_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("items", sa.Column("steam_item_nameid", sa.String(length=80), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("items", "steam_item_nameid")
