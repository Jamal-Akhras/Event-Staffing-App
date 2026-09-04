from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ManagerInvitation:
    invitation_id: str
    organisation_id: str
    email: str
    role: str
    venue_scope: tuple[str, ...] | None
    token: str
    created_by_user_id: str
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None
    accepted_user_id: str | None = None

    def __post_init__(self) -> None:
        if self.role not in ("admin", "manager"):
            raise ValueError("Invitations carry the admin or manager role.")
        if self.role == "manager" and not self.venue_scope:
            raise ValueError("A manager invitation names at least one venue.")
        if (self.accepted_at is None) != (self.accepted_user_id is None):
            raise ValueError("Acceptance records its time and user together.")

    def is_open(self, now: datetime) -> bool:
        return self.accepted_at is None and now < self.expires_at
