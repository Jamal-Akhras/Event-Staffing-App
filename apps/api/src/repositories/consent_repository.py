from __future__ import annotations

from typing import Protocol

from apps.api.src.models.consent import ConsentEvent


class ConsentRepository(Protocol):
    def append(self, event: ConsentEvent) -> ConsentEvent: ...
    def list_for_user(self, user_id: str) -> list[ConsentEvent]: ...
    def latest_for_purpose(self, user_id: str, purpose: str) -> ConsentEvent | None: ...
