from __future__ import annotations

from typing import Protocol

from apps.api.src.models.booking_charge_adjustment import BookingChargeAdjustment


class BookingChargeAdjustmentRepository(Protocol):
    def record(self, adjustment: BookingChargeAdjustment) -> BookingChargeAdjustment: ...

    def list_for_charge(self, charge_id: str) -> list[BookingChargeAdjustment]: ...

    def list_for_charges(self, charge_ids: list[str]) -> list[BookingChargeAdjustment]: ...
