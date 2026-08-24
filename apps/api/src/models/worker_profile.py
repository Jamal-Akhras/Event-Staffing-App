from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class WorkerProfile:
    worker_id: str
    display_name: str
    role: str
    city: str
    experience_years: int
    reliability_score: float
    badges: list[str]
    bio: str | None
    languages: list[str]
    email: str | None
    phone: str | None
    address: str | None
    emergency_contact: str | None
    pay_rate: Decimal | None
    notes: str | None
    updated_at: datetime
    avatar_url: str | None = None
    allow_venue_recontact: bool = False
    market_id: str | None = None
