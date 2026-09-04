from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from apps.api.src.models.consent import (
    PURPOSE_PRIVACY,
    PURPOSE_PROFILING,
    PURPOSE_TERMS,
    ConsentEvent,
)
from apps.api.src.repositories.consent_repository import ConsentRepository

POLICY_VERSION = "2026-09"
GRANTABLE_PURPOSES = (PURPOSE_PROFILING,)


class ConsentService:
    def __init__(self, consents: ConsentRepository) -> None:
        self._consents = consents

    def record_registration(self, user_id: str, now: datetime) -> None:
        for purpose in (PURPOSE_TERMS, PURPOSE_PRIVACY):
            self._append(user_id, purpose, "acknowledged", "contract", "registration", now)

    def set_profiling(self, user_id: str, granted: bool, now: datetime) -> ConsentEvent:
        action = "granted" if granted else "withdrawn"
        return self._append(user_id, PURPOSE_PROFILING, action, "consent", "self_service", now)

    def has_active_consent(self, user_id: str, purpose: str) -> bool:
        latest = self._consents.latest_for_purpose(user_id, purpose)
        return latest is not None and latest.action == "granted"

    def current_state(self, user_id: str) -> dict[str, str]:
        state: dict[str, str] = {}
        for event in self._consents.list_for_user(user_id):
            state[event.purpose] = event.action
        return state

    def _append(
        self, user_id: str, purpose: str, action: str, basis: str, source: str, now: datetime
    ) -> ConsentEvent:
        return self._consents.append(
            ConsentEvent(
                event_id=str(uuid4()),
                user_id=user_id,
                purpose=purpose,
                action=action,
                basis=basis,
                policy_version=POLICY_VERSION,
                source=source,
                occurred_at=now,
            )
        )
