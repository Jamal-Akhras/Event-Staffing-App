from __future__ import annotations

from apps.api.src.models.booking_charge import BookingCharge


class InMemoryBookingChargeRepository:
    def __init__(self) -> None:
        self._charges: dict[str, BookingCharge] = {}

    def record(self, charge: BookingCharge) -> BookingCharge:
        self._charges[charge.booking_id] = charge
        return charge

    def get_for_booking(self, booking_id: str) -> BookingCharge | None:
        return self._charges.get(booking_id)

    def list_for_account(self, account_id: str, period: str | None = None) -> list[BookingCharge]:
        return sorted(
            (
                charge
                for charge in self._charges.values()
                if charge.account_id == account_id and (period is None or charge.period == period)
            ),
            key=lambda charge: charge.completed_at,
        )

    def list_for_worker(self, worker_id: str) -> list[BookingCharge]:
        return sorted(
            (charge for charge in self._charges.values() if charge.worker_id == worker_id),
            key=lambda charge: charge.completed_at,
        )

    def clear(self) -> None:
        self._charges.clear()
