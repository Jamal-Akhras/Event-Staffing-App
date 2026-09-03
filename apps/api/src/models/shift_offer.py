from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

OFFER_SOURCES = ("rota", "cover", "manual")
OFFER_STATUSES = ("pending", "accepted", "declined", "withdrawn", "expired")
RESPONSE_SOURCES = ("manual", "auto")
ANSWERED_STATUSES = ("accepted", "declined", "withdrawn")


@dataclass(frozen=True)
class ShiftOffer:
    offer_id: str
    shift_id: str
    venue_id: str
    worker_id: str
    source: str
    status: str
    offered_at: datetime
    expires_at: datetime | None = None
    responded_at: datetime | None = None
    response_source: str | None = None

    def __post_init__(self) -> None:
        if self.source not in OFFER_SOURCES:
            raise ValueError(f"Unknown offer source '{self.source}'.")
        if self.status not in OFFER_STATUSES:
            raise ValueError(f"Unknown offer status '{self.status}'.")
        if self.status in ANSWERED_STATUSES and self.responded_at is None:
            raise ValueError("An answered offer requires its response time.")
        if self.status in ("pending", "expired") and self.responded_at is not None:
            raise ValueError("Only answered offers carry a response time.")
        if self.response_source is not None and self.response_source not in RESPONSE_SOURCES:
            raise ValueError(f"Unknown response source '{self.response_source}'.")
        if self.response_source is not None and self.status != "accepted":
            raise ValueError("Only an accepted offer carries a response source.")
        if self.status == "accepted" and self.response_source is None:
            raise ValueError("An accepted offer records how it was accepted.")
