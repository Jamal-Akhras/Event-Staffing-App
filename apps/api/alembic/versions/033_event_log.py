from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("organisation_id", sa.String(), nullable=True),
        sa.Column("venue_id", sa.String(), nullable=True),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("subject_type", sa.String(length=40), nullable=True),
        sa.Column("subject_id", sa.String(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
        sa.Column("app_version", sa.String(length=40), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_events_occurred", "events", ["occurred_at"])
    op.create_index("ix_events_recorded", "events", ["recorded_at", "event_id"])
    op.create_index("ix_events_name_occurred", "events", ["name", "occurred_at"])
    op.create_index("ix_events_actor_occurred", "events", ["actor_user_id", "occurred_at"])
    op.create_index("ix_events_venue_occurred", "events", ["venue_id", "occurred_at"])
    op.create_index("ix_events_worker_occurred", "events", ["worker_id", "occurred_at"])
    op.create_index("ix_events_subject", "events", ["subject_type", "subject_id", "occurred_at"])
    op.create_index("ix_events_category_occurred", "events", ["category", "occurred_at"])
    if bind.dialect.name == "postgresql":
        op.execute("REVOKE UPDATE, DELETE ON events FROM PUBLIC")


def downgrade() -> None:
    op.drop_table("events")
