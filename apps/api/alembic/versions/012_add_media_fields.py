from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return column in [c["name"] for c in inspect(conn).get_columns(table)]


def upgrade() -> None:
    bind = op.get_bind()

    for col, type_ in [
        ("venue_type", sa.String()),
        ("contact_email", sa.String()),
        ("contact_phone", sa.String()),
        ("default_location", sa.String()),
        ("avatar_url", sa.String()),
        ("photos", sa.JSON()),
    ]:
        if not _has_column(bind, "accounts", col):
            op.add_column("accounts", sa.Column(col, type_, nullable=True))

    if not _has_column(bind, "worker_profiles", "avatar_url"):
        op.add_column("worker_profiles", sa.Column("avatar_url", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()

    for col in ["venue_type", "contact_email", "contact_phone", "default_location", "avatar_url", "photos"]:
        if _has_column(bind, "accounts", col):
            op.drop_column("accounts", col)

    if _has_column(bind, "worker_profiles", "avatar_url"):
        op.drop_column("worker_profiles", "avatar_url")
