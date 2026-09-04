from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "053"
down_revision = "052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("booking_charges") as batch:
        batch.add_column(sa.Column("fee_basis", sa.String(length=24), nullable=True))
        batch.add_column(sa.Column("source_venue_id", sa.String(), nullable=True))
    with op.batch_alter_table("bookings") as batch:
        batch.add_column(sa.Column("allocation_source", sa.String(length=16), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("bookings") as batch:
        batch.drop_column("allocation_source")
    with op.batch_alter_table("booking_charges") as batch:
        batch.drop_column("source_venue_id")
        batch.drop_column("fee_basis")
