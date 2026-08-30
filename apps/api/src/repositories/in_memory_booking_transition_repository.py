from __future__ import annotations

from apps.api.src.models.booking_transition import BookingTransition


class InMemoryBookingTransitionRepository:
    def __init__(self) -> None:
        self._transitions: list[BookingTransition] = []

    def append(self, transition: BookingTransition) -> BookingTransition:
        self._transitions.append(transition)
        return transition

    def list_for_booking(self, booking_id: str) -> list[BookingTransition]:
        return sorted(
            (item for item in self._transitions if item.booking_id == booking_id),
            key=lambda item: item.occurred_at,
        )

    def clear(self) -> None:
        self._transitions.clear()
