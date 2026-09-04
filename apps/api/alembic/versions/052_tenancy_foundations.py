from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organisation_memberships") as batch:
        batch.add_column(sa.Column("venue_scope", sa.JSON(), nullable=True))

    op.create_table(
        "manager_invitations",
        sa.Column("invitation_id", sa.String(), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.String(),
            sa.ForeignKey("organisations.organisation_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(length=12), nullable=False),
        sa.Column("venue_scope", sa.JSON(), nullable=True),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("expires_at", UtcDateTime(), nullable=False),
        sa.Column("accepted_at", UtcDateTime(), nullable=True),
        sa.Column("accepted_user_id", sa.String(), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'manager')", name="ck_manager_invitations_role"),
        sa.CheckConstraint(
            "(accepted_at IS NULL) = (accepted_user_id IS NULL)",
            name="ck_manager_invitations_acceptance",
        ),
    )
    op.create_index(
        "ix_manager_invitations_org", "manager_invitations", ["organisation_id", "created_at"]
    )

    op.create_table(
        "notification_receipts",
        sa.Column(
            "notification_id",
            sa.String(),
            sa.ForeignKey("notifications.notification_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("read_at", UtcDateTime(), nullable=False),
    )
    op.create_index("ix_notification_receipts_user", "notification_receipts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notification_receipts_user", table_name="notification_receipts")
    op.drop_table("notification_receipts")
    op.drop_index("ix_manager_invitations_org", table_name="manager_invitations")
    op.drop_table("manager_invitations")
    with op.batch_alter_table("organisation_memberships") as batch:
        batch.drop_column("venue_scope")
