from __future__ import annotations

import secrets

from alembic import op
import sqlalchemy as sa

revision = "032"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bookings") as batch:
        batch.add_column(sa.Column("check_in_code", sa.String(length=4), nullable=True))
        batch.add_column(sa.Column("completion_code", sa.String(length=4), nullable=True))
    connection = op.get_bind()
    booking_ids = connection.execute(sa.text("SELECT booking_id FROM bookings WHERE check_in_code IS NULL")).scalars().all()
    for booking_id in booking_ids:
        check_in_code = f"{secrets.randbelow(10_000):04d}"
        completion_code = f"{secrets.randbelow(10_000):04d}"
        while completion_code == check_in_code:
            completion_code = f"{secrets.randbelow(10_000):04d}"
        connection.execute(
            sa.text("UPDATE bookings SET check_in_code = :check_in, completion_code = :completion WHERE booking_id = :booking_id"),
            {
                "check_in": check_in_code,
                "completion": completion_code,
                "booking_id": booking_id,
            },
        )
    with op.batch_alter_table("bookings") as batch:
        batch.alter_column("check_in_code", existing_type=sa.String(length=4), nullable=False)
        batch.alter_column("completion_code", existing_type=sa.String(length=4), nullable=False)
        batch.create_check_constraint("ck_bookings_check_in_code_length", "length(check_in_code) = 4")
        batch.create_check_constraint("ck_bookings_completion_code_length", "length(completion_code) = 4")
        batch.create_check_constraint("ck_bookings_attendance_codes_distinct", "check_in_code <> completion_code")


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch:
        batch.drop_constraint("ck_bookings_attendance_codes_distinct", type_="check")
        batch.drop_constraint("ck_bookings_completion_code_length", type_="check")
        batch.drop_constraint("ck_bookings_check_in_code_length", type_="check")
        batch.drop_column("completion_code")
        batch.drop_column("check_in_code")
