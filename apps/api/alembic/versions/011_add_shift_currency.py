"""Add currency column to shifts table

Revision ID: 011
Revises: 010
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return column in [c["name"] for c in inspect(conn).get_columns(table)]


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "shifts", "currency"):
        op.add_column("shifts", sa.Column("currency", sa.String(3), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "shifts", "currency"):
        op.drop_column("shifts", "currency")
