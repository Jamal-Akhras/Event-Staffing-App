from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "005_add_shift_templates"
down_revision = "004_add_workers_needed_to_shifts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create shift_templates table
    op.create_table(
        "shift_templates",
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("pay_rate", sa.Float(), nullable=False),
        sa.Column("workers_needed", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("template_id"),
    )

    # Create recurring_schedules table
    op.create_table(
        "recurring_schedules",
        sa.Column("schedule_id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("time_of_day", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_generated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("schedule_id"),
    )


def downgrade() -> None:
    op.drop_table("recurring_schedules")
    op.drop_table("shift_templates")
