from __future__ import annotations

from alembic import op

revision = "045"
down_revision = "044"
branch_labels = None
depends_on = None

_NEW = (
    "'worker_unavailable', 'worker_illness', 'worker_double_booked', 'venue_overstaffed', "
    "'venue_event_cancelled', 'shift_details_changed', 'missed_check_in', "
    "'rota_published', 'venue_recorded', 'hours_adjusted', 'other'"
)
_OLD = (
    "'worker_unavailable', 'worker_illness', 'worker_double_booked', 'venue_overstaffed', "
    "'venue_event_cancelled', 'shift_details_changed', 'missed_check_in', 'other'"
)


def _swap_reason_check(reasons: str) -> None:
    with op.batch_alter_table("booking_transitions") as batch:
        batch.drop_constraint("ck_booking_transitions_reason", type_="check")
        batch.create_check_constraint(
            "ck_booking_transitions_reason",
            f"reason_code IS NULL OR reason_code IN ({reasons})",
        )


def upgrade() -> None:
    _swap_reason_check(_NEW)


def downgrade() -> None:
    _swap_reason_check(_OLD)
