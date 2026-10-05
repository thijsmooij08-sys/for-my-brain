"""initial paper fills

Revision ID: 0001_initial_fills
Revises:
Create Date: 2026-10-03
"""
import sqlalchemy as sa

from alembic import op

revision = "0001_initial_fills"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("token_id", sa.String(length=200), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("quantity", sa.String(length=40), nullable=False),
        sa.Column("price", sa.String(length=40), nullable=False),
        sa.Column("fee", sa.String(length=40), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fills")
