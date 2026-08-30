from __future__ import annotations

from typing import Protocol

from apps.api.src.models.booking_transition import BookingTransition


class BookingTransitionRepository(Protocol):
    def append(self, transition: BookingTransition) -> BookingTransition: ...

    def list_for_booking(self, booking_id: str) -> list[BookingTransition]: ...
