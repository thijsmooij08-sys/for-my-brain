"""add provenance evidence records

Revision ID: 0002_evidence
Revises: 0001_initial_fills
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_evidence"
down_revision = "0001_initial_fills"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "evidence" not in inspector.get_table_names():
        op.create_table(
            "evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provenance_key", sa.String(length=64), nullable=False),
            sa.Column("source", sa.String(length=100), nullable=False),
            sa.Column("source_type", sa.String(length=100), nullable=False),
            sa.Column("source_url", sa.String(length=500), nullable=True),
            sa.Column("source_timestamp", sa.String(length=50), nullable=False),
            sa.Column("collected_at", sa.String(length=50), nullable=False),
            sa.Column("value", sa.String(length=10000), nullable=False),
            sa.Column("revision", sa.String(length=100), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("market_id", sa.String(length=200), nullable=True),
            sa.Column("token_id", sa.String(length=200), nullable=True),
            sa.Column("event_id", sa.String(length=200), nullable=True),
            sa.Column("confidence", sa.String(length=40), nullable=False),
            sa.Column("model_version", sa.String(length=100), nullable=True),
        )
    if not any(index["name"] == "ix_evidence_provenance_key" for index in inspector.get_indexes("evidence")):
        op.create_index("ix_evidence_provenance_key", "evidence", ["provenance_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_evidence_provenance_key", table_name="evidence")
    op.drop_table("evidence")
