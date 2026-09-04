from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.api.src.models.shift_offer import ShiftOffer


class DuplicatePendingOfferError(Exception):
    pass


class ShiftOfferRepository(Protocol):
    def save(self, offer: ShiftOffer) -> ShiftOffer: ...

    def get(self, offer_id: str) -> ShiftOffer | None: ...

    def get_pending_for_shift(self, shift_id: str) -> ShiftOffer | None: ...

    def list_for_worker(self, worker_id: str) -> list[ShiftOffer]: ...

    def list_pending_for_worker(self, worker_id: str) -> list[ShiftOffer]: ...

    def claim_pending_unexpired(self, now: datetime) -> list[ShiftOffer]: ...
