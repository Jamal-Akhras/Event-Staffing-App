"""Add email verification to users

Revision ID: 019
Revises: 018
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(conn).get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "users", "email_verified"):
        op.add_column(
            "users",
            sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column(bind, "users", "email_verification_token"):
        op.add_column(
            "users",
            sa.Column("email_verification_token", sa.String(), nullable=True),
        )
        op.create_index(
            "ix_users_email_verification_token",
            "users",
            ["email_verification_token"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "users", "email_verification_token"):
        op.drop_index("ix_users_email_verification_token", table_name="users")
        op.drop_column("users", "email_verification_token")
    if _has_column(bind, "users", "email_verified"):
        op.drop_column("users", "email_verified")
