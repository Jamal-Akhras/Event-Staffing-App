from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ShiftTemplate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template_id: str
    operator_id: str
    name: str
    role: str
    location: str
    duration_hours: float
    pay_rate: Decimal
    workers_needed: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
    account_id: str | None = None


class RecurringSchedule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    schedule_id: str
    template_id: str
    operator_id: str
    frequency: str  # "daily", "weekly", "monthly"
    day_of_week: int | None  # 0-6 for weekly schedules
    time_of_day: str  # "HH:MM" format (e.g., "18:00")
    start_date: datetime
    end_date: datetime | None
    is_active: bool
    created_at: datetime
    last_generated_at: datetime | None
