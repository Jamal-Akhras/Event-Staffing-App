"""Add notification_preferences to accounts

Revision ID: 018
Revises: 017
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(conn).get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "accounts", "notification_preferences"):
        op.add_column("accounts", sa.Column("notification_preferences", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "accounts", "notification_preferences"):
        op.drop_column("accounts", "notification_preferences")
