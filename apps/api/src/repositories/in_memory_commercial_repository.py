from __future__ import annotations

from apps.api.src.models.commercial import (
    CommercialAgreement,
    ShiftBoost,
    SubscriptionCharge,
)
from apps.api.src.repositories.commercial_repository import (
    DuplicateActiveBoostError,
    DuplicateSubscriptionChargeError,
)


class InMemoryCommercialAgreementRepository:
    def __init__(self) -> None:
        self._items: dict[str, CommercialAgreement] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, agreement: CommercialAgreement) -> CommercialAgreement:
        self._items[agreement.agreement_id] = agreement
        return agreement

    def list_for_organisation(self, organisation_id: str) -> list[CommercialAgreement]:
        rows = [a for a in self._items.values() if a.organisation_id == organisation_id]
        return sorted(rows, key=lambda a: a.effective_from)


class InMemorySubscriptionChargeRepository:
    def __init__(self) -> None:
        self._items: dict[str, SubscriptionCharge] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, charge: SubscriptionCharge) -> SubscriptionCharge:
        if self.get_for_venue_period(charge.venue_id, charge.period) is not None:
            raise DuplicateSubscriptionChargeError(charge.venue_id)
        self._items[charge.subscription_charge_id] = charge
        return charge

    def get_for_venue_period(self, venue_id: str, period: str) -> SubscriptionCharge | None:
        for charge in self._items.values():
            if charge.venue_id == venue_id and charge.period == period:
                return charge
        return None

    def list_for_organisation_period(
        self, organisation_id: str, period: str
    ) -> list[SubscriptionCharge]:
        rows = [
            charge
            for charge in self._items.values()
            if charge.organisation_id == organisation_id and charge.period == period
        ]
        return sorted(rows, key=lambda charge: charge.venue_id)


class InMemoryShiftBoostRepository:
    def __init__(self) -> None:
        self._items: dict[str, ShiftBoost] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, boost: ShiftBoost) -> ShiftBoost:
        if boost.status == "active":
            existing = self.get_active_for_shift(boost.shift_id)
            if existing is not None and existing.boost_id != boost.boost_id:
                raise DuplicateActiveBoostError(boost.shift_id)
        self._items[boost.boost_id] = boost
        return boost

    def get_active_for_shift(self, shift_id: str) -> ShiftBoost | None:
        for boost in self._items.values():
            if boost.shift_id == shift_id and boost.status == "active":
                return boost
        return None

    def list_for_venue_period(self, venue_id: str, period: str) -> list[ShiftBoost]:
        rows = [
            boost
            for boost in self._items.values()
            if boost.venue_id == venue_id and boost.period == period
        ]
        return sorted(rows, key=lambda boost: boost.purchased_at)
