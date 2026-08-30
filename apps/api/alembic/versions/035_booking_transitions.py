from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.models.booking_transition import REASON_CODES

revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None

_REASONS = ", ".join(f"'{code}'" for code in REASON_CODES)


def upgrade() -> None:
    op.create_table(
        "booking_transitions",
        sa.Column("transition_id", sa.String(), primary_key=True),
        sa.Column("booking_id", sa.String(), nullable=False),
        sa.Column("from_state", sa.String(length=30), nullable=True),
        sa.Column("to_state", sa.String(length=30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("reason_code", sa.String(length=40), nullable=True),
        sa.Column("reason_note", sa.String(length=500), nullable=True),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.booking_id"], ondelete="CASCADE"),
        sa.CheckConstraint(f"reason_code IS NULL OR reason_code IN ({_REASONS})", name="ck_booking_transitions_reason"),
        sa.CheckConstraint(
            "actor_role IS NULL OR actor_role IN ('worker', 'operator', 'system')",
            name="ck_booking_transitions_actor_role",
        ),
    )
    op.create_index("ix_booking_transitions_booking", "booking_transitions", ["booking_id", "occurred_at"])
    op.create_index("ix_booking_transitions_state_occurred", "booking_transitions", ["to_state", "occurred_at"])


def downgrade() -> None:
    op.drop_table("booking_transitions")
