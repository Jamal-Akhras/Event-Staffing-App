from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "054"
down_revision = "053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_agreements",
        sa.Column("agreement_id", sa.String(), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.String(),
            sa.ForeignKey("organisations.organisation_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("plan", sa.String(length=16), nullable=False),
        sa.Column("monthly_fee_per_site", sa.Numeric(12, 2), nullable=False),
        sa.Column("own_pool_fee_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("outside_fee_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_from", UtcDateTime(), nullable=False),
        sa.Column("effective_until", UtcDateTime(), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=True),
        sa.CheckConstraint(
            "plan IN ('classic', 'plus', 'enterprise')", name="ck_commercial_agreements_plan"
        ),
        sa.CheckConstraint(
            "monthly_fee_per_site >= 0", name="ck_commercial_agreements_monthly_fee"
        ),
        sa.CheckConstraint(
            "own_pool_fee_percent >= 0 AND own_pool_fee_percent <= 100",
            name="ck_commercial_agreements_own_pool",
        ),
        sa.CheckConstraint(
            "outside_fee_percent >= 0 AND outside_fee_percent <= 100",
            name="ck_commercial_agreements_outside",
        ),
    )
    op.create_index(
        "ix_commercial_agreements_org",
        "commercial_agreements",
        ["organisation_id", "effective_from"],
    )

    op.create_table(
        "subscription_charges",
        sa.Column("subscription_charge_id", sa.String(), primary_key=True),
        sa.Column("organisation_id", sa.String(), nullable=False),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agreement_id", sa.String(), nullable=False),
        sa.Column("plan", sa.String(length=16), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("coverage_start", UtcDateTime(), nullable=False),
        sa.Column("coverage_end", UtcDateTime(), nullable=False),
        sa.Column("minted_at", UtcDateTime(), nullable=False),
        sa.UniqueConstraint("venue_id", "period", name="uq_subscription_charges_venue_period"),
        sa.CheckConstraint("amount >= 0", name="ck_subscription_charges_amount"),
    )
    op.create_index(
        "ix_subscription_charges_org_period",
        "subscription_charges",
        ["organisation_id", "period"],
    )

    op.create_table(
        "shift_boosts",
        sa.Column("boost_id", sa.String(), primary_key=True),
        sa.Column(
            "shift_id",
            sa.String(),
            sa.ForeignKey("shifts.shift_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("venue_id", sa.String(), nullable=False),
        sa.Column("tier", sa.String(length=8), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("purchased_by_user_id", sa.String(), nullable=False),
        sa.Column("purchased_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint("tier IN ('top1', 'top5', 'top10')", name="ck_shift_boosts_tier"),
        sa.CheckConstraint("price >= 0", name="ck_shift_boosts_price"),
        sa.CheckConstraint(
            "status IN ('active', 'cancelled')", name="ck_shift_boosts_status"
        ),
    )
    op.create_index("ix_shift_boosts_venue_period", "shift_boosts", ["venue_id", "period"])
    bind = op.get_bind()
    where = sa.text("status = 'active'")
    if bind.dialect.name == "postgresql":
        op.create_index(
            "uq_shift_boosts_one_active", "shift_boosts", ["shift_id"],
            unique=True, postgresql_where=where,
        )
    else:
        op.create_index(
            "uq_shift_boosts_one_active", "shift_boosts", ["shift_id"],
            unique=True, sqlite_where=where,
        )

    with op.batch_alter_table("booking_charges") as batch:
        batch.add_column(sa.Column("plan", sa.String(length=16), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("booking_charges") as batch:
        batch.drop_column("plan")
    op.drop_index("uq_shift_boosts_one_active", table_name="shift_boosts")
    op.drop_index("ix_shift_boosts_venue_period", table_name="shift_boosts")
    op.drop_table("shift_boosts")
    op.drop_index("ix_subscription_charges_org_period", table_name="subscription_charges")
    op.drop_table("subscription_charges")
    op.drop_index("ix_commercial_agreements_org", table_name="commercial_agreements")
    op.drop_table("commercial_agreements")
