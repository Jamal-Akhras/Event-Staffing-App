from __future__ import annotations

from typing import Protocol

from apps.api.src.models.shift_change_request import ShiftChangeRequest, ShiftChangeTransition

PENDING_STATUSES = ("pending_replacement", "pending_manager")


class DuplicatePendingChangeError(Exception):
    pass


class ShiftChangeRequestRepository(Protocol):
    def save(self, request: ShiftChangeRequest) -> ShiftChangeRequest: ...

    def get(self, request_id: str) -> ShiftChangeRequest | None: ...

    def get_pending_for_booking(self, booking_id: str) -> ShiftChangeRequest | None: ...

    def list_for_worker(self, worker_id: str) -> list[ShiftChangeRequest]: ...

    def list_for_venue(
        self, venue_id: str, status: str | None = None
    ) -> list[ShiftChangeRequest]: ...

    def list_pending(self) -> list[ShiftChangeRequest]: ...


class ShiftChangeTransitionRepository(Protocol):
    def append(self, transition: ShiftChangeTransition) -> ShiftChangeTransition: ...

    def list_for_request(self, request_id: str) -> list[ShiftChangeTransition]: ...
