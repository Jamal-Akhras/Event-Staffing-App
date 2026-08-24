from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("bookings", sa.Column("cancellation_reason", sa.String(length=500), nullable=True))
    op.add_column("bookings", sa.Column("cancelled_by_user_id", sa.String(), nullable=True))
    op.add_column("applications", sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("applications", sa.Column("withdrawal_reason", sa.String(length=500), nullable=True))
    op.add_column(
        "shifts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("shifts", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("shifts", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("shifts", sa.Column("cancellation_reason", sa.String(length=500), nullable=True))
    op.add_column("shifts", sa.Column("cancelled_by_user_id", sa.String(), nullable=True))
    bind.execute(sa.text("UPDATE shifts SET updated_at = created_at WHERE updated_at IS NULL"))

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("applications") as batch:
            batch.drop_constraint("ck_applications_status", type_="check")
            batch.create_check_constraint(
                "ck_applications_status",
                "status IN ('applied', 'approved', 'rejected', 'withdrawn')",
            )
        with op.batch_alter_table("shifts") as batch:
            batch.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)
            batch.create_check_constraint(
                "ck_shifts_status",
                "status IN ('open', 'filled', 'closed', 'cancelled')",
            )
        return

    op.drop_constraint("ck_applications_status", "applications", type_="check")
    op.create_check_constraint(
        "ck_applications_status",
        "applications",
        "status IN ('applied', 'approved', 'rejected', 'withdrawn')",
    )
    op.alter_column("shifts", "updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.create_check_constraint(
        "ck_shifts_status",
        "shifts",
        "status IN ('open', 'filled', 'closed', 'cancelled')",
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE applications SET status = 'rejected', decided_at = COALESCE(decided_at, withdrawn_at) "
            "WHERE status = 'withdrawn'"
        )
    )
    bind.execute(sa.text("UPDATE shifts SET status = 'closed' WHERE status = 'cancelled'"))

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("shifts") as batch:
            batch.drop_constraint("ck_shifts_status", type_="check")
            batch.drop_column("cancelled_by_user_id")
            batch.drop_column("cancellation_reason")
            batch.drop_column("cancelled_at")
            batch.drop_column("closed_at")
            batch.drop_column("updated_at")
        with op.batch_alter_table("applications") as batch:
            batch.drop_constraint("ck_applications_status", type_="check")
            batch.create_check_constraint(
                "ck_applications_status",
                "status IN ('applied', 'approved', 'rejected')",
            )
            batch.drop_column("withdrawal_reason")
            batch.drop_column("withdrawn_at")
        with op.batch_alter_table("bookings") as batch:
            batch.drop_column("cancelled_by_user_id")
            batch.drop_column("cancellation_reason")
        return

    op.drop_constraint("ck_shifts_status", "shifts", type_="check")
    op.drop_column("shifts", "cancelled_by_user_id")
    op.drop_column("shifts", "cancellation_reason")
    op.drop_column("shifts", "cancelled_at")
    op.drop_column("shifts", "closed_at")
    op.drop_column("shifts", "updated_at")
    op.drop_constraint("ck_applications_status", "applications", type_="check")
    op.create_check_constraint(
        "ck_applications_status",
        "applications",
        "status IN ('applied', 'approved', 'rejected')",
    )
    op.drop_column("applications", "withdrawal_reason")
    op.drop_column("applications", "withdrawn_at")
    op.drop_column("bookings", "cancelled_by_user_id")
    op.drop_column("bookings", "cancellation_reason")
