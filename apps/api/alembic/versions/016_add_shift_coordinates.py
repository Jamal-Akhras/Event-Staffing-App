"""Add latitude and longitude to shifts

Revision ID: 016
Revises: 015
Create Date: 2026-05-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(conn).get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "shifts", "latitude"):
        op.add_column("shifts", sa.Column("latitude", sa.Float(), nullable=True))
    if not _has_column(bind, "shifts", "longitude"):
        op.add_column("shifts", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "shifts", "longitude"):
        op.drop_column("shifts", "longitude")
    if _has_column(bind, "shifts", "latitude"):
        op.drop_column("shifts", "latitude")
