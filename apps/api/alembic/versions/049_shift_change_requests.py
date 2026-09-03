from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "049"
down_revision = "048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shift_change_requests",
        sa.Column("request_id", sa.String(), primary_key=True),
        sa.Column("booking_id", sa.String(), nullable=False),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("venue_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("change_type", sa.String(length=12), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("replacement_worker_id", sa.String(), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("updated_at", UtcDateTime(), nullable=False),
        sa.Column("decided_at", UtcDateTime(), nullable=True),
        sa.Column("decided_by_user_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.booking_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.shift_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.venue_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("change_type IN ('release', 'cover')", name="ck_shift_changes_type"),
        sa.CheckConstraint(
            "status IN ('pending_replacement', 'pending_manager', 'approved', 'declined', "
            "'withdrawn', 'expired')",
            name="ck_shift_changes_status",
        ),
        sa.CheckConstraint(
            "(change_type = 'cover') = (replacement_worker_id IS NOT NULL)",
            name="ck_shift_changes_replacement",
        ),
        sa.CheckConstraint(
            "(status IN ('approved', 'declined')) = "
            "(decided_at IS NOT NULL AND decided_by_user_id IS NOT NULL)",
            name="ck_shift_changes_decision",
        ),
        sa.CheckConstraint(
            "status <> 'pending_replacement' OR change_type = 'cover'",
            name="ck_shift_changes_replacement_wait",
        ),
    )
    op.create_index("ix_shift_changes_worker", "shift_change_requests", ["worker_id", "created_at"])
    op.create_index("ix_shift_changes_venue_status", "shift_change_requests", ["venue_id", "status"])
    bind = op.get_bind()
    where = sa.text("status IN ('pending_replacement', 'pending_manager')")
    if bind.dialect.name == "postgresql":
        op.create_index(
            "uq_shift_changes_one_pending", "shift_change_requests", ["booking_id"],
            unique=True, postgresql_where=where,
        )
    else:
        op.create_index(
            "uq_shift_changes_one_pending", "shift_change_requests", ["booking_id"],
            unique=True, sqlite_where=where,
        )

    op.create_table(
        "shift_change_request_transitions",
        sa.Column("transition_id", sa.String(), primary_key=True),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("from_status", sa.String(length=24), nullable=True),
        sa.Column("to_status", sa.String(length=24), nullable=False),
        sa.Column("occurred_at", UtcDateTime(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_id"], ["shift_change_requests.request_id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_shift_change_transitions_request",
        "shift_change_request_transitions",
        ["request_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_shift_change_transitions_request", table_name="shift_change_request_transitions"
    )
    op.drop_table("shift_change_request_transitions")
    op.drop_index("uq_shift_changes_one_pending", table_name="shift_change_requests")
    op.drop_index("ix_shift_changes_venue_status", table_name="shift_change_requests")
    op.drop_index("ix_shift_changes_worker", table_name="shift_change_requests")
    op.drop_table("shift_change_requests")
