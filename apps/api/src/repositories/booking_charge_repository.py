from __future__ import annotations

from typing import Protocol

from apps.api.src.models.booking_charge import BookingCharge


class BookingChargeRepository(Protocol):
    def record(self, charge: BookingCharge) -> BookingCharge: ...

    def get_for_booking(self, booking_id: str) -> BookingCharge | None: ...

    def list_for_account(self, account_id: str, period: str | None = None) -> list[BookingCharge]: ...

    def list_for_worker(self, worker_id: str) -> list[BookingCharge]: ...
