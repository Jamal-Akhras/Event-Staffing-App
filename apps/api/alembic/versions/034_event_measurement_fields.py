from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("events") as batch:
        batch.add_column(sa.Column("slate_id", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("position", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("dwell_ms", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_events_slate", "events", ["slate_id"])


def downgrade() -> None:
    op.drop_index("ix_events_slate", table_name="events")
    with op.batch_alter_table("events") as batch:
        batch.drop_column("event_version")
        batch.drop_column("dwell_ms")
        batch.drop_column("position")
        batch.drop_column("slate_id")
