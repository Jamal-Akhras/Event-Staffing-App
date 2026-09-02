from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("booking_charges") as batch:
        batch.add_column(sa.Column("worker_relationship", sa.String(length=20), nullable=True))
    op.execute(
        sa.text("UPDATE booking_charges SET worker_relationship = 'one_off' WHERE worker_relationship IS NULL")
    )


def downgrade() -> None:
    with op.batch_alter_table("booking_charges") as batch:
        batch.drop_column("worker_relationship")
