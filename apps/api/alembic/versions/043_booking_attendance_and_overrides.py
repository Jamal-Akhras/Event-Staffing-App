from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime

revision = "043"
down_revision = "042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bookings") as batch:
        batch.add_column(
            sa.Column("attendance_mode", sa.String(12), nullable=False, server_default="pin")
        )
        batch.add_column(sa.Column("override_checked_in_at", UtcDateTime(), nullable=True))
        batch.add_column(sa.Column("override_checked_out_at", UtcDateTime(), nullable=True))
        batch.create_check_constraint(
            "ck_bookings_attendance_mode", "attendance_mode IN ('pin', 'employed')"
        )
        batch.create_check_constraint(
            "ck_bookings_override_pair",
            "(override_checked_in_at IS NULL) = (override_checked_out_at IS NULL)",
        )
        batch.create_check_constraint(
            "ck_bookings_override_order",
            "override_checked_out_at IS NULL OR override_checked_out_at > override_checked_in_at",
        )


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch:
        batch.drop_constraint("ck_bookings_override_order", type_="check")
        batch.drop_constraint("ck_bookings_override_pair", type_="check")
        batch.drop_constraint("ck_bookings_attendance_mode", type_="check")
        batch.drop_column("override_checked_out_at")
        batch.drop_column("override_checked_in_at")
        batch.drop_column("attendance_mode")
