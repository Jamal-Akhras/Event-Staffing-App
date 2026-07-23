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
    account_id: str | None  # set for operators, None for workers
    worker_profile_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    password_changed_at: datetime | None = None
    email_verified: bool = False
    email_verification_token: str | None = None
