from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "reports",
        sa.Column("report_id", sa.String(), primary_key=True),
        sa.Column("reporter_user_id", sa.String(), nullable=False),
        sa.Column("reporter_role", sa.String(length=20), nullable=False),
        sa.Column("subject_type", sa.String(length=30), nullable=False),
        sa.Column("subject_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="submitted"),
        sa.Column("resolution_notes", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["users.user_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("reporter_role IN ('worker', 'operator')", name="ck_reports_reporter_role"),
        sa.CheckConstraint(
            "subject_type IN ('venue', 'shift', 'application', 'booking', 'message')",
            name="ck_reports_subject_type",
        ),
        sa.CheckConstraint(
            "category IN ('safety', 'harassment', 'payment', 'no_show', 'fraud', 'other')",
            name="ck_reports_category",
        ),
        sa.CheckConstraint(
            "status IN ('submitted', 'reviewing', 'resolved', 'dismissed')",
            name="ck_reports_status",
        ),
    )
    op.create_index("ix_reports_reporter_created", "reports", ["reporter_user_id", "created_at"])
    op.create_index("ix_reports_subject", "reports", ["subject_type", "subject_id"])
    op.create_index("ix_reports_status_created", "reports", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_reports_status_created", table_name="reports")
    op.drop_index("ix_reports_subject", table_name="reports")
    op.drop_index("ix_reports_reporter_created", table_name="reports")
    op.drop_table("reports")
    op.drop_column("users", "anonymized_at")
    op.drop_column("users", "deactivated_at")
