"""Add accounts table and account_id to users, shifts, shift_templates

Revision ID: 010
Revises: 009_add_worker_feed_state
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010"
down_revision = "009_add_worker_feed_state"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return column in [c["name"] for c in inspect(conn).get_columns(table)]


def _has_index(conn, table: str, index: str) -> bool:
    return index in [i["name"] for i in inspect(conn).get_indexes(table)]


def upgrade() -> None:
    bind = op.get_bind()

    # accounts table — safe to skip if already exists (created by create_all)
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )

    if not _has_column(bind, "users", "account_id"):
        op.add_column("users", sa.Column("account_id", sa.String(), sa.ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True))
    if not _has_index(bind, "users", "ix_users_account_id"):
        op.create_index("ix_users_account_id", "users", ["account_id"])

    if not _has_column(bind, "shifts", "account_id"):
        op.add_column("shifts", sa.Column("account_id", sa.String(), sa.ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True))
    if not _has_index(bind, "shifts", "ix_shifts_account_id"):
        op.create_index("ix_shifts_account_id", "shifts", ["account_id"])

    if not _has_column(bind, "shift_templates", "account_id"):
        op.add_column("shift_templates", sa.Column("account_id", sa.String(), sa.ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True))
    if not _has_index(bind, "shift_templates", "ix_shift_templates_account_id"):
        op.create_index("ix_shift_templates_account_id", "shift_templates", ["account_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_index(bind, "shift_templates", "ix_shift_templates_account_id"):
        op.drop_index("ix_shift_templates_account_id", "shift_templates")
    if _has_column(bind, "shift_templates", "account_id"):
        op.drop_column("shift_templates", "account_id")
    if _has_index(bind, "shifts", "ix_shifts_account_id"):
        op.drop_index("ix_shifts_account_id", "shifts")
    if _has_column(bind, "shifts", "account_id"):
        op.drop_column("shifts", "account_id")
    if _has_index(bind, "users", "ix_users_account_id"):
        op.drop_index("ix_users_account_id", "users")
    if _has_column(bind, "users", "account_id"):
        op.drop_column("users", "account_id")
    op.drop_table("accounts")
