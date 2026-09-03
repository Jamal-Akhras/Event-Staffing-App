from __future__ import annotations

from apps.api.src.models.shift_change_request import ShiftChangeRequest, ShiftChangeTransition
from apps.api.src.repositories.shift_change_request_repository import (
    DuplicatePendingChangeError,
    PENDING_STATUSES,
)


class InMemoryShiftChangeRequestRepository:
    def __init__(self) -> None:
        self._requests: dict[str, ShiftChangeRequest] = {}

    def save(self, request: ShiftChangeRequest) -> ShiftChangeRequest:
        if request.status in PENDING_STATUSES:
            existing = self.get_pending_for_booking(request.booking_id)
            if existing is not None and existing.request_id != request.request_id:
                raise DuplicatePendingChangeError(
                    f"Booking {request.booking_id} already has an open change request."
                )
        self._requests[request.request_id] = request
        return request

    def get(self, request_id: str) -> ShiftChangeRequest | None:
        return self._requests.get(request_id)

    def get_pending_for_booking(self, booking_id: str) -> ShiftChangeRequest | None:
        for request in self._requests.values():
            if request.booking_id == booking_id and request.status in PENDING_STATUSES:
                return request
        return None

    def list_for_worker(self, worker_id: str) -> list[ShiftChangeRequest]:
        items = [
            request
            for request in self._requests.values()
            if request.worker_id == worker_id or request.replacement_worker_id == worker_id
        ]
        return sorted(items, key=lambda request: request.created_at, reverse=True)

    def list_for_venue(self, venue_id: str, status: str | None = None) -> list[ShiftChangeRequest]:
        items = [
            request
            for request in self._requests.values()
            if request.venue_id == venue_id and (status is None or request.status == status)
        ]
        return sorted(items, key=lambda request: request.created_at)

    def list_pending(self) -> list[ShiftChangeRequest]:
        return sorted(
            (r for r in self._requests.values() if r.status in PENDING_STATUSES),
            key=lambda request: request.created_at,
        )

    def clear(self) -> None:
        self._requests.clear()


class InMemoryShiftChangeTransitionRepository:
    def __init__(self) -> None:
        self._transitions: list[ShiftChangeTransition] = []

    def append(self, transition: ShiftChangeTransition) -> ShiftChangeTransition:
        self._transitions.append(transition)
        return transition

    def list_for_request(self, request_id: str) -> list[ShiftChangeTransition]:
        return sorted(
            (t for t in self._transitions if t.request_id == request_id),
            key=lambda t: t.occurred_at,
        )

    def clear(self) -> None:
        self._transitions.clear()
