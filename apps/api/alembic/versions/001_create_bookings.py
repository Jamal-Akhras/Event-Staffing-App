from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from packages.domain.src.booking_state import BookingState

revision = "001_create_bookings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("booking_id", sa.String(), primary_key=True),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("state", sa.Enum(BookingState), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("no_show_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("bookings")
    if op.get_bind().dialect.name == "postgresql":
        sa.Enum(BookingState, name="bookingstate").drop(op.get_bind(), checkfirst=True)
