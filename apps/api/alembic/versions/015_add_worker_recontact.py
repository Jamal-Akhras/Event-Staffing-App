from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspect(conn).get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "worker_profiles", "allow_venue_recontact"):
        op.add_column(
            "worker_profiles",
            sa.Column("allow_venue_recontact", sa.Boolean(), nullable=False, server_default="false"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "worker_profiles", "allow_venue_recontact"):
        op.drop_column("worker_profiles", "allow_venue_recontact")
