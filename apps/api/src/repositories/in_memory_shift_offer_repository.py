from __future__ import annotations

from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.shift_offer_repository import DuplicatePendingOfferError


class InMemoryShiftOfferRepository:
    def __init__(self) -> None:
        self._offers: dict[str, ShiftOffer] = {}

    def save(self, offer: ShiftOffer) -> ShiftOffer:
        if offer.status == "pending":
            existing = self.get_pending_for_shift(offer.shift_id)
            if existing is not None and existing.offer_id != offer.offer_id:
                raise DuplicatePendingOfferError(
                    f"Shift {offer.shift_id} already has a pending offer."
                )
        self._offers[offer.offer_id] = offer
        return offer

    def get(self, offer_id: str) -> ShiftOffer | None:
        return self._offers.get(offer_id)

    def get_pending_for_shift(self, shift_id: str) -> ShiftOffer | None:
        for offer in self._offers.values():
            if offer.shift_id == shift_id and offer.status == "pending":
                return offer
        return None

    def list_for_worker(self, worker_id: str) -> list[ShiftOffer]:
        return sorted(
            (offer for offer in self._offers.values() if offer.worker_id == worker_id),
            key=lambda offer: offer.offered_at,
            reverse=True,
        )

    def list_pending_for_worker(self, worker_id: str) -> list[ShiftOffer]:
        return [offer for offer in self.list_for_worker(worker_id) if offer.status == "pending"]

    def clear(self) -> None:
        self._offers.clear()
