from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_certifications",
        sa.Column("certification_id", sa.String(), primary_key=True),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("expires_at", UtcDateTime(), nullable=False),
        sa.Column("reference", sa.String(length=120), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("updated_at", UtcDateTime(), nullable=False),
        sa.UniqueConstraint("worker_id", "name", name="uq_worker_certifications_worker_name"),
    )
    op.create_index(
        "ix_worker_certifications_expiry", "worker_certifications", ["worker_id", "expires_at"]
    )
    with op.batch_alter_table("shifts") as batch:
        batch.add_column(sa.Column("required_certification", sa.String(length=120), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.drop_column("required_certification")
    op.drop_index("ix_worker_certifications_expiry", table_name="worker_certifications")
    op.drop_table("worker_certifications")
