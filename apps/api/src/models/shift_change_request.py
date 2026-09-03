from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CHANGE_TYPES = ("release", "cover")
CHANGE_STATUSES = (
    "pending_replacement",
    "pending_manager",
    "approved",
    "declined",
    "withdrawn",
    "expired",
)
DECIDED_STATUSES = ("approved", "declined")


@dataclass(frozen=True)
class ShiftChangeRequest:
    request_id: str
    booking_id: str
    shift_id: str
    venue_id: str
    worker_id: str
    change_type: str
    status: str
    reason: str
    created_at: datetime
    updated_at: datetime
    replacement_worker_id: str | None = None
    decided_at: datetime | None = None
    decided_by_user_id: str | None = None

    def __post_init__(self) -> None:
        if self.change_type not in CHANGE_TYPES:
            raise ValueError(f"Unknown change type '{self.change_type}'.")
        if self.status not in CHANGE_STATUSES:
            raise ValueError(f"Unknown change status '{self.status}'.")
        if self.change_type == "cover" and self.replacement_worker_id is None:
            raise ValueError("A cover request names its replacement worker.")
        if self.change_type == "release" and self.replacement_worker_id is not None:
            raise ValueError("A release request has no replacement worker.")
        if self.status == "pending_replacement" and self.change_type != "cover":
            raise ValueError("Only a cover request waits on its replacement.")
        decided = self.status in DECIDED_STATUSES
        if decided and (self.decided_at is None or self.decided_by_user_id is None):
            raise ValueError("A decided request records its time and decider.")
        if not decided and (self.decided_at is not None or self.decided_by_user_id is not None):
            raise ValueError("Decision metadata belongs only on decided requests.")


@dataclass(frozen=True)
class ShiftChangeTransition:
    transition_id: str
    request_id: str
    to_status: str
    occurred_at: datetime
    from_status: str | None = None
    actor_user_id: str | None = None
    actor_role: str | None = None
    note: str | None = None
