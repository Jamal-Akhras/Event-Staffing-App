from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("bookings") as batch:
            batch.add_column(sa.Column("payment_method", sa.String(length=30), nullable=True))
            batch.add_column(sa.Column("payment_reference", sa.String(length=200), nullable=True))
            batch.add_column(sa.Column("payment_recorded_by_user_id", sa.String(), nullable=True))
            batch.create_check_constraint(
                "ck_bookings_payment_method",
                "payment_method IS NULL OR payment_method IN ('bank_transfer', 'cash', 'payroll', 'other')",
            )
        return
    op.add_column("bookings", sa.Column("payment_method", sa.String(length=30), nullable=True))
    op.add_column("bookings", sa.Column("payment_reference", sa.String(length=200), nullable=True))
    op.add_column("bookings", sa.Column("payment_recorded_by_user_id", sa.String(), nullable=True))
    op.create_check_constraint(
        "ck_bookings_payment_method",
        "bookings",
        "payment_method IS NULL OR payment_method IN ('bank_transfer', 'cash', 'payroll', 'other')",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("bookings") as batch:
            batch.drop_constraint("ck_bookings_payment_method", type_="check")
            batch.drop_column("payment_recorded_by_user_id")
            batch.drop_column("payment_reference")
            batch.drop_column("payment_method")
        return
    op.drop_constraint("ck_bookings_payment_method", "bookings", type_="check")
    op.drop_column("bookings", "payment_recorded_by_user_id")
    op.drop_column("bookings", "payment_reference")
    op.drop_column("bookings", "payment_method")
