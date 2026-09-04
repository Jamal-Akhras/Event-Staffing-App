from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.api.src.models.commercial import CommercialAgreement, ShiftBoost, SubscriptionCharge
from apps.api.src.repositories.commercial_repository import (
    CommercialAgreementRepository,
    DuplicateActiveBoostError,
    DuplicateSubscriptionChargeError,
    ShiftBoostRepository,
    SubscriptionChargeRepository,
)
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.services.billing_math import money
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from apps.api.src.services.plan_catalogue import boost_price, plan_price


def agreement_as_of(
    agreements: CommercialAgreementRepository,
    organisation: str,
    currency: str,
    at: datetime,
) -> CommercialAgreement:
    active = [
        agreement
        for agreement in agreements.list_for_organisation(organisation)
        if agreement.effective_from <= at
        and (agreement.effective_until is None or at < agreement.effective_until)
    ]
    if active:
        return max(active, key=lambda agreement: agreement.effective_from)
    price = plan_price("classic")
    return CommercialAgreement(
        agreement_id=f"default-classic-{organisation}",
        organisation_id=organisation,
        plan="classic",
        monthly_fee_per_site=price.monthly_fee_per_site,
        own_pool_fee_percent=price.own_pool_fee_percent,
        outside_fee_percent=price.outside_fee_percent,
        currency=currency,
        effective_from=at,
        effective_until=None,
        created_at=at,
    )


def fee_percent_for(agreement: CommercialAgreement, fee_basis: str) -> Decimal:
    if fee_basis in ("venue_employed", "organisation_employed"):
        return Decimal("0.00")
    if fee_basis == "venue_pool":
        return agreement.own_pool_fee_percent
    return agreement.outside_fee_percent


class CommercialService:
    def __init__(
        self,
        agreements: CommercialAgreementRepository,
        subscriptions: SubscriptionChargeRepository,
        boosts: ShiftBoostRepository,
        organisations: OrganisationRepository,
        shifts: ShiftRepository,
    ) -> None:
        self._agreements = agreements
        self._subscriptions = subscriptions
        self._boosts = boosts
        self._organisations = organisations
        self._shifts = shifts

    def current_agreement(self, organisation_id: str, now: datetime) -> CommercialAgreement:
        organisation = self._organisations.get_organisation(organisation_id)
        currency = organisation.currency if organisation is not None else "GBP"
        return agreement_as_of(self._agreements, organisation_id, currency, now)

    def change_plan(
        self, organisation_id: str, plan: str, actor_user_id: str, now: datetime
    ) -> CommercialAgreement:
        organisation = self._organisations.get_organisation(organisation_id)
        if organisation is None:
            raise NotFoundError("Organisation not found.")
        if plan == "enterprise":
            raise ValidationError("Enterprise agreements are configured by Venue OS, not self-served.")
        price = plan_price(plan)
        current = self.current_agreement(organisation_id, now)
        if current.plan == plan and not current.agreement_id.startswith("default-classic-"):
            return current
        for agreement in self._agreements.list_for_organisation(organisation_id):
            if agreement.effective_until is None:
                self._agreements.save(replace(agreement, effective_until=now))
        return self._agreements.save(
            CommercialAgreement(
                agreement_id=str(uuid4()),
                organisation_id=organisation_id,
                plan=plan,
                monthly_fee_per_site=price.monthly_fee_per_site,
                own_pool_fee_percent=price.own_pool_fee_percent,
                outside_fee_percent=price.outside_fee_percent,
                currency=organisation.currency,
                effective_from=now,
                effective_until=None,
                created_at=now,
                created_by_user_id=actor_user_id,
            )
        )

    def purchase_boost(
        self, shift_id: str, venue_id: str, tier: str, actor_user_id: str, now: datetime
    ) -> ShiftBoost:
        shift = self._shifts.get(shift_id)
        if shift is None or shift.account_id != venue_id:
            raise NotFoundError("That shift was not found.")
        if shift.status == "cancelled":
            raise ValidationError("A cancelled shift cannot be boosted.")
        boost = ShiftBoost(
            boost_id=str(uuid4()),
            shift_id=shift_id,
            venue_id=venue_id,
            tier=tier,
            price=money(boost_price(tier)),
            currency=shift.currency,
            period=now.strftime("%Y-%m"),
            status="active",
            purchased_by_user_id=actor_user_id,
            purchased_at=now,
        )
        try:
            return self._boosts.save(boost)
        except DuplicateActiveBoostError as exc:
            raise ConflictError("This shift already has an active boost.") from exc

    def mint_subscriptions(self, organisation_id: str, period: str, now: datetime) -> int:
        organisation = self._organisations.get_organisation(organisation_id)
        if organisation is None:
            return 0
        agreement = self.current_agreement(organisation_id, now)
        if agreement.monthly_fee_per_site <= 0:
            return 0
        coverage_start = _period_start(period)
        coverage_end = now
        minted = 0
        for venue in self._organisations.list_venues_for_organisation(organisation_id):
            try:
                self._subscriptions.save(
                    SubscriptionCharge(
                        subscription_charge_id=str(uuid4()),
                        organisation_id=organisation_id,
                        venue_id=venue.venue_id,
                        agreement_id=agreement.agreement_id,
                        plan=agreement.plan,
                        period=period,
                        amount=money(agreement.monthly_fee_per_site),
                        currency=agreement.currency,
                        coverage_start=coverage_start,
                        coverage_end=coverage_end,
                        minted_at=now,
                    )
                )
                minted += 1
            except DuplicateSubscriptionChargeError:
                continue
        return minted


def _period_start(period: str) -> datetime:
    from datetime import UTC

    year, month = period.split("-")
    return datetime(int(year), int(month), 1, tzinfo=UTC)
