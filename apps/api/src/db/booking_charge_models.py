from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Numeric, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class BookingChargeModel(Base):
    __tablename__ = "booking_charges"
    __table_args__ = (
        CheckConstraint("hours >= 0", name="ck_booking_charges_hours"),
        CheckConstraint("fee_percent >= 0 AND fee_percent <= 100", name="ck_booking_charges_fee_percent"),
        CheckConstraint("total = wages + fee", name="ck_booking_charges_total"),
        Index("ix_booking_charges_account_period", "account_id", "period"),
        Index("ix_booking_charges_account_completed", "account_id", "completed_at"),
        Index("ix_booking_charges_worker_completed", "worker_id", "completed_at"),
    )

    charge_id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, unique=True)
    shift_id = Column(String, nullable=False)
    account_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
    worker_name = Column(String(160), nullable=False)
    role = Column(String(80), nullable=False)
    period = Column(String(7), nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    completed_at = Column(UtcDateTime(), nullable=False)
    hours = Column(Numeric(6, 2), nullable=False)
    pay_rate = Column(Numeric(12, 2), nullable=False)
    wages = Column(Numeric(12, 2), nullable=False)
    fee_percent = Column(Numeric(5, 2), nullable=False)
    fee = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    fee_waived = Column(Boolean, nullable=False, default=False)
    waiver_code = Column(String(40), nullable=True)
    fee_basis = Column(String(24), nullable=True)
    source_venue_id = Column(String, nullable=True)
    plan = Column(String(16), nullable=True)
    recorded_at = Column(UtcDateTime(), nullable=False)
    worker_relationship = Column(String(20), nullable=True)


class BookingChargeAdjustmentModel(Base):
    __tablename__ = "booking_charge_adjustments"
    __table_args__ = (
        CheckConstraint("delta_hours <> 0", name="ck_adjustment_deltas_present"),
        Index("ix_charge_adjustments_charge", "charge_id"),
    )

    adjustment_id = Column(String, primary_key=True)
    charge_id = Column(String, ForeignKey("booking_charges.charge_id", ondelete="RESTRICT"), nullable=False)
    booking_id = Column(String, nullable=False)
    delta_hours = Column(Numeric(6, 2), nullable=False)
    delta_wages = Column(Numeric(12, 2), nullable=False)
    delta_fee = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(500), nullable=False)
    created_by_user_id = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
