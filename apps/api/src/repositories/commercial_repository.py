from __future__ import annotations

from typing import Protocol

from apps.api.src.models.commercial import (
    CommercialAgreement,
    ShiftBoost,
    SubscriptionCharge,
)


class DuplicateActiveBoostError(Exception):
    pass


class DuplicateSubscriptionChargeError(Exception):
    pass


class CommercialAgreementRepository(Protocol):
    def save(self, agreement: CommercialAgreement) -> CommercialAgreement: ...
    def list_for_organisation(self, organisation_id: str) -> list[CommercialAgreement]: ...


class SubscriptionChargeRepository(Protocol):
    def save(self, charge: SubscriptionCharge) -> SubscriptionCharge: ...
    def get_for_venue_period(self, venue_id: str, period: str) -> SubscriptionCharge | None: ...
    def list_for_organisation_period(
        self, organisation_id: str, period: str
    ) -> list[SubscriptionCharge]: ...


class ShiftBoostRepository(Protocol):
    def save(self, boost: ShiftBoost) -> ShiftBoost: ...
    def get_active_for_shift(self, shift_id: str) -> ShiftBoost | None: ...
    def list_for_venue_period(self, venue_id: str, period: str) -> list[ShiftBoost]: ...
