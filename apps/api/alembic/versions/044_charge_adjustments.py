from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime

revision = "044"
down_revision = "043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_charge_adjustments",
        sa.Column("adjustment_id", sa.String(), primary_key=True),
        sa.Column(
            "charge_id",
            sa.String(),
            sa.ForeignKey("booking_charges.charge_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("booking_id", sa.String(), nullable=False),
        sa.Column("delta_hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("delta_wages", sa.Numeric(12, 2), nullable=False),
        sa.Column("delta_fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint("delta_hours <> 0", name="ck_adjustment_deltas_present"),
    )
    op.create_index("ix_charge_adjustments_charge", "booking_charge_adjustments", ["charge_id"])


def downgrade() -> None:
    op.drop_index("ix_charge_adjustments_charge", table_name="booking_charge_adjustments")
    op.drop_table("booking_charge_adjustments")
