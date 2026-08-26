from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "006_add_messages"
down_revision = "005_add_shift_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=True),
        sa.Column("booking_id", sa.String(), nullable=True),
        sa.Column("sender_id", sa.String(), nullable=False),
        sa.Column("sender_role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("message_id"),
    )


    op.create_index("ix_messages_shift_id", "messages", ["shift_id"])
    op.create_index("ix_messages_application_id", "messages", ["application_id"])
    op.create_index("ix_messages_booking_id", "messages", ["booking_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_booking_id", table_name="messages")
    op.drop_index("ix_messages_application_id", table_name="messages")
    op.drop_index("ix_messages_shift_id", table_name="messages")
    op.drop_table("messages")
