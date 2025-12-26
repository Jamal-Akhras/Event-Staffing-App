from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    """Domain model for a user account."""

    user_id: str
    email: str
    hashed_password: str
    role: str  # "operator" or "worker"
    worker_profile_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
