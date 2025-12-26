from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_create_core_tables"
down_revision = "001_create_bookings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shifts",
        sa.Column("shift_id", sa.String(), primary_key=True),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("pay_rate", sa.Float(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "applications",
        sa.Column("application_id", sa.String(), primary_key=True),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("booking_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "worker_profiles",
        sa.Column("worker_id", sa.String(), primary_key=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("badges", sa.JSON(), nullable=False),
        sa.Column("bio", sa.String(), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("emergency_contact", sa.String(), nullable=True),
        sa.Column("pay_rate", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("worker_profiles")
    op.drop_table("applications")
    op.drop_table("shifts")
