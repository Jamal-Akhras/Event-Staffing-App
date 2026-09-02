from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime

revision = "039"
down_revision = "038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.add_column(
            sa.Column("origin", sa.String(length=20), nullable=False, server_default="market")
        )
        batch.add_column(sa.Column("assigned_worker_id", sa.String(), nullable=True))
        batch.add_column(
            sa.Column("billable", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch.add_column(sa.Column("offer_pool_at", UtcDateTime(), nullable=True))
        batch.add_column(sa.Column("publish_market_at", UtcDateTime(), nullable=True))
        batch.create_check_constraint("ck_shifts_origin", "origin IN ('assigned', 'pool', 'market')")
        batch.create_check_constraint(
            "ck_shifts_assigned_has_worker",
            "origin <> 'assigned' OR assigned_worker_id IS NOT NULL",
        )
    op.create_index("ix_shifts_assigned_worker_id", "shifts", ["assigned_worker_id"])

    with op.batch_alter_table("venues") as batch:
        batch.add_column(sa.Column("escalation_policy", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("venues") as batch:
        batch.drop_column("escalation_policy")

    op.drop_index("ix_shifts_assigned_worker_id", table_name="shifts")
    with op.batch_alter_table("shifts") as batch:
        batch.drop_constraint("ck_shifts_assigned_has_worker", type_="check")
        batch.drop_constraint("ck_shifts_origin", type_="check")
        batch.drop_column("publish_market_at")
        batch.drop_column("offer_pool_at")
        batch.drop_column("billable")
        batch.drop_column("assigned_worker_id")
        batch.drop_column("origin")
