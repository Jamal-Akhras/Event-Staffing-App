from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "056"
down_revision = "055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consent_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=12), nullable=False),
        sa.Column("basis", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint(
            "action IN ('granted', 'withdrawn', 'objected', 'acknowledged')",
            name="ck_consent_events_action",
        ),
    )
    op.create_index(
        "ix_consent_events_user_purpose",
        "consent_events",
        ["user_id", "purpose", "occurred_at"],
    )
    with op.batch_alter_table("shifts") as batch:
        batch.add_column(sa.Column("risk_information", sa.String(length=2000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.drop_column("risk_information")
    op.drop_index("ix_consent_events_user_purpose", table_name="consent_events")
    op.drop_table("consent_events")
