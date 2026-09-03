from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "048"
down_revision = "047"
branch_labels = None
depends_on = None

_NEW_REASONS = (
    "'worker_unavailable', 'worker_illness', 'worker_double_booked', 'venue_overstaffed', "
    "'venue_event_cancelled', 'shift_details_changed', 'missed_check_in', "
    "'rota_published', 'venue_recorded', 'hours_adjusted', "
    "'offer_accepted', 'cover_approved', 'release_approved', 'other'"
)
_OLD_REASONS = (
    "'worker_unavailable', 'worker_illness', 'worker_double_booked', 'venue_overstaffed', "
    "'venue_event_cancelled', 'shift_details_changed', 'missed_check_in', "
    "'rota_published', 'venue_recorded', 'hours_adjusted', 'other'"
)


def _swap_reason_check(reasons: str) -> None:
    with op.batch_alter_table("booking_transitions") as batch:
        batch.drop_constraint("ck_booking_transitions_reason", type_="check")
        batch.create_check_constraint(
            "ck_booking_transitions_reason",
            f"reason_code IS NULL OR reason_code IN ({reasons})",
        )


def upgrade() -> None:
    op.create_table(
        "shift_offers",
        sa.Column("offer_id", sa.String(), primary_key=True),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("venue_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(length=12), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("offered_at", UtcDateTime(), nullable=False),
        sa.Column("expires_at", UtcDateTime(), nullable=True),
        sa.Column("responded_at", UtcDateTime(), nullable=True),
        sa.Column("response_source", sa.String(length=12), nullable=True),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.shift_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.venue_id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "source IN ('rota', 'cover', 'manual')", name="ck_shift_offers_source"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="ck_shift_offers_status",
        ),
        sa.CheckConstraint(
            "response_source IS NULL OR response_source IN ('manual', 'auto')",
            name="ck_shift_offers_response_source",
        ),
        sa.CheckConstraint(
            "(status IN ('accepted', 'declined', 'withdrawn')) = (responded_at IS NOT NULL)",
            name="ck_shift_offers_answer_time",
        ),
        sa.CheckConstraint(
            "(response_source IS NOT NULL) = (status = 'accepted')",
            name="ck_shift_offers_accept_source",
        ),
    )
    op.create_index("ix_shift_offers_worker", "shift_offers", ["worker_id", "offered_at"])
    op.create_index("ix_shift_offers_shift", "shift_offers", ["shift_id"])
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "uq_shift_offers_one_pending",
            "shift_offers",
            ["shift_id"],
            unique=True,
            postgresql_where=sa.text("status = 'pending'"),
        )
    else:
        op.create_index(
            "uq_shift_offers_one_pending",
            "shift_offers",
            ["shift_id"],
            unique=True,
            sqlite_where=sa.text("status = 'pending'"),
        )
    _swap_reason_check(_NEW_REASONS)


def downgrade() -> None:
    _swap_reason_check(_OLD_REASONS)
    op.drop_index("uq_shift_offers_one_pending", table_name="shift_offers")
    op.drop_index("ix_shift_offers_shift", table_name="shift_offers")
    op.drop_index("ix_shift_offers_worker", table_name="shift_offers")
    op.drop_table("shift_offers")
