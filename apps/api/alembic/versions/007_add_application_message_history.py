from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "007_message_history"
down_revision = "006_add_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create application_message_history table
    op.create_table(
        "application_message_history",
        sa.Column("history_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("edited_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("history_id"),
    )

    # Create index for faster lookups by application_id
    op.create_index("ix_app_msg_history_application_id", "application_message_history", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_app_msg_history_application_id", table_name="application_message_history")
    op.drop_table("application_message_history")
