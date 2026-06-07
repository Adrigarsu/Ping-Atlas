"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-07

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "targets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("host", sa.String(255), nullable=False, unique=True),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "probes",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rtt_ms", sa.Float(), nullable=True),
        sa.Column("packet_loss", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", "started_at"),
    )

    op.create_table(
        "hops",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("probe_id", UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl", sa.Integer(), nullable=False),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("rtt_ms", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("country", sa.String(255), nullable=True),
        sa.Column("asn", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "started_at"),
    )

    op.execute("SELECT create_hypertable('probes', 'started_at')")
    op.execute("SELECT create_hypertable('hops', 'started_at')")


def downgrade() -> None:
    op.drop_table("hops")
    op.drop_table("probes")
    op.drop_table("targets")