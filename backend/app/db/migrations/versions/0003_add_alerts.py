"""add alerts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-07

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("target_id", UUID(as_uuid=True), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("probe_id", UUID(as_uuid=True), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rtt_ms", sa.Float(), nullable=False),
        sa.Column("rolling_avg_ms", sa.Float(), nullable=False),
        sa.Column("delta_ms", sa.Float(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="FALSE"),
    )
    op.create_index("ix_alerts_target_id", "alerts", ["target_id"])
    op.create_index("ix_alerts_triggered_at", "alerts", ["triggered_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_triggered_at", "alerts")
    op.drop_index("ix_alerts_target_id", "alerts")
    op.drop_table("alerts")