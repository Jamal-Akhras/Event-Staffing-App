from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import synonym

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class ShiftTemplateModel(Base):
    __tablename__ = "shift_templates"
    __table_args__ = (
        CheckConstraint("duration_hours > 0", name="ck_shift_templates_duration_positive"),
        CheckConstraint("pay_rate >= 0", name="ck_shift_templates_pay_rate_nonnegative"),
        CheckConstraint("workers_needed >= 1", name="ck_shift_templates_workers_needed_positive"),
    )

    template_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=True, index=True)
    account_id = synonym("venue_id")
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    duration_hours = Column(Float, nullable=False)
    pay_rate = Column(Numeric(12, 2), nullable=False)
    workers_needed = Column(Integer, nullable=False, default=1)
    notes = Column(String, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)


class RecurringScheduleModel(Base):
    __tablename__ = "recurring_schedules"
    __table_args__ = (
        CheckConstraint("frequency IN ('daily', 'weekly', 'monthly')", name="ck_recurring_schedules_frequency"),
        CheckConstraint(
            "day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)",
            name="ck_recurring_schedules_day_of_week",
        ),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_recurring_schedules_date_order"),
    )

    schedule_id = Column(String, primary_key=True)
    template_id = Column(
        String,
        ForeignKey("shift_templates.template_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operator_id = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=True)
    time_of_day = Column(String, nullable=False)
    start_date = Column(UtcDateTime(), nullable=False)
    end_date = Column(UtcDateTime(), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(UtcDateTime(), nullable=False)
    last_generated_at = Column(UtcDateTime(), nullable=True)
