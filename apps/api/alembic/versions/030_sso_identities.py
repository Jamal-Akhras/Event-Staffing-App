from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "030"
down_revision = "029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("sso_provider", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("sso_subject", sa.String(length=255), nullable=True))
    op.create_index(
        "ux_users_sso_identity",
        "users",
        ["sso_provider", "sso_subject"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_users_sso_identity", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("sso_subject")
        batch.drop_column("sso_provider")
