from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, get_args

ReasonCode = Literal[
    "worker_unavailable",
    "worker_illness",
    "worker_double_booked",
    "venue_overstaffed",
    "venue_event_cancelled",
    "shift_details_changed",
    "missed_check_in",
    "other",
]

REASON_CODES: tuple[str, ...] = get_args(ReasonCode)


@dataclass(frozen=True)
class BookingTransition:
    transition_id: str
    booking_id: str
    to_state: str
    occurred_at: datetime
    from_state: str | None = None
    actor_user_id: str | None = None
    actor_role: str | None = None
    reason_code: str | None = None
    reason_note: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
