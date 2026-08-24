from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch:
            batch.add_column(
                sa.Column("session_version", sa.Integer(), nullable=False, server_default="0")
            )
            batch.create_check_constraint(
                "ck_users_session_version_nonnegative",
                "session_version >= 0",
            )
        return
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_users_session_version_nonnegative", "users", "session_version >= 0")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch:
            batch.drop_constraint("ck_users_session_version_nonnegative", type_="check")
            batch.drop_column("session_version")
        return
    op.drop_constraint("ck_users_session_version_nonnegative", "users", type_="check")
    op.drop_column("users", "session_version")
