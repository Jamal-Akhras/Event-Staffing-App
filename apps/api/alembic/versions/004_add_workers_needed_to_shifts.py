from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004_add_workers_needed_to_shifts"
down_revision = "003_create_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add workers_needed and workers_filled columns to shifts table
    op.add_column("shifts", sa.Column("workers_needed", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("shifts", sa.Column("workers_filled", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("shifts", "workers_filled")
    op.drop_column("shifts", "workers_needed")
