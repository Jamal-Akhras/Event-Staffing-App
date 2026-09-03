from __future__ import annotations

from apps.api.src.models.booking_charge_adjustment import BookingChargeAdjustment


class InMemoryBookingChargeAdjustmentRepository:
    def __init__(self) -> None:
        self._adjustments: list[BookingChargeAdjustment] = []

    def record(self, adjustment: BookingChargeAdjustment) -> BookingChargeAdjustment:
        self._adjustments.append(adjustment)
        return adjustment

    def list_for_charge(self, charge_id: str) -> list[BookingChargeAdjustment]:
        return sorted(
            (item for item in self._adjustments if item.charge_id == charge_id),
            key=lambda item: item.created_at,
        )

    def list_for_charges(self, charge_ids: list[str]) -> list[BookingChargeAdjustment]:
        wanted = set(charge_ids)
        return sorted(
            (item for item in self._adjustments if item.charge_id in wanted),
            key=lambda item: item.created_at,
        )

    def clear(self) -> None:
        self._adjustments.clear()
