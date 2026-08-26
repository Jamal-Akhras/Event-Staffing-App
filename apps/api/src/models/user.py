from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    user_id: str
    email: str
    hashed_password: str
    role: str
    account_id: str | None
    worker_profile_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    password_changed_at: datetime | None = None
    email_verified: bool = False
    email_verification_token: str | None = None
    session_version: int = 0
    deactivated_at: datetime | None = None
    anonymized_at: datetime | None = None
    sso_provider: str | None = None
    sso_subject: str | None = None
