from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class CommercialAgreementModel(Base):
    __tablename__ = "commercial_agreements"
    __table_args__ = (
        CheckConstraint(
            "plan IN ('classic', 'plus', 'enterprise')", name="ck_commercial_agreements_plan"
        ),
        CheckConstraint("monthly_fee_per_site >= 0", name="ck_commercial_agreements_monthly_fee"),
        CheckConstraint(
            "own_pool_fee_percent >= 0 AND own_pool_fee_percent <= 100",
            name="ck_commercial_agreements_own_pool",
        ),
        CheckConstraint(
            "outside_fee_percent >= 0 AND outside_fee_percent <= 100",
            name="ck_commercial_agreements_outside",
        ),
        Index("ix_commercial_agreements_org", "organisation_id", "effective_from"),
    )

    agreement_id = Column(String, primary_key=True)
    organisation_id = Column(
        String, ForeignKey("organisations.organisation_id", ondelete="RESTRICT"), nullable=False
    )
    plan = Column(String(16), nullable=False)
    monthly_fee_per_site = Column(Numeric(12, 2), nullable=False)
    own_pool_fee_percent = Column(Numeric(5, 2), nullable=False)
    outside_fee_percent = Column(Numeric(5, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    effective_from = Column(UtcDateTime(), nullable=False)
    effective_until = Column(UtcDateTime(), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    created_by_user_id = Column(String, nullable=True)


class SubscriptionChargeModel(Base):
    __tablename__ = "subscription_charges"
    __table_args__ = (
        UniqueConstraint("venue_id", "period", name="uq_subscription_charges_venue_period"),
        CheckConstraint("amount >= 0", name="ck_subscription_charges_amount"),
        Index("ix_subscription_charges_org_period", "organisation_id", "period"),
    )

    subscription_charge_id = Column(String, primary_key=True)
    organisation_id = Column(String, nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="CASCADE"), nullable=False)
    agreement_id = Column(String, nullable=False)
    plan = Column(String(16), nullable=False)
    period = Column(String(7), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    coverage_start = Column(UtcDateTime(), nullable=False)
    coverage_end = Column(UtcDateTime(), nullable=False)
    minted_at = Column(UtcDateTime(), nullable=False)


class ShiftBoostModel(Base):
    __tablename__ = "shift_boosts"
    __table_args__ = (
        CheckConstraint("tier IN ('top1', 'top5', 'top10')", name="ck_shift_boosts_tier"),
        CheckConstraint("price >= 0", name="ck_shift_boosts_price"),
        CheckConstraint("status IN ('active', 'cancelled')", name="ck_shift_boosts_status"),
        Index("ix_shift_boosts_venue_period", "venue_id", "period"),
        Index(
            "uq_shift_boosts_one_active",
            "shift_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    boost_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="RESTRICT"), nullable=False)
    venue_id = Column(String, nullable=False)
    tier = Column(String(8), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    period = Column(String(7), nullable=False)
    status = Column(String(12), nullable=False)
    purchased_by_user_id = Column(String, nullable=False)
    purchased_at = Column(UtcDateTime(), nullable=False)
