from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def _has_table(conn, table: str) -> bool:
    return table in inspect(conn).get_table_names()


def _has_index(conn, table: str, index: str) -> bool:
    return any(ix["name"] == index for ix in inspect(conn).get_indexes(table))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, "notifications"):
        op.create_table(
            "notifications",
            sa.Column("notification_id", sa.String(), primary_key=True),
            sa.Column("worker_id", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("body", sa.String(), nullable=False),
            sa.Column("shift_id", sa.String(), nullable=True),
            sa.Column("read", sa.Boolean(), nullable=False, default=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    if not _has_index(bind, "notifications", "ix_notifications_worker_id"):
        op.create_index("ix_notifications_worker_id", "notifications", ["worker_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "notifications"):
        op.drop_index("ix_notifications_worker_id", table_name="notifications")
        op.drop_table("notifications")
