from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.commercial import CommercialAgreement, ShiftBoost
from apps.api.src.models.organisation import Organisation
from apps.api.src.repositories.commercial_repository import (
    DuplicateActiveBoostError,
    DuplicateSubscriptionChargeError,
)
from apps.api.src.repositories.in_memory_commercial_repository import (
    InMemoryCommercialAgreementRepository,
    InMemoryShiftBoostRepository,
    InMemorySubscriptionChargeRepository,
)
from apps.api.src.repositories.in_memory_organisation_repository import (
    InMemoryOrganisationRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.models.organisation import Venue
from apps.api.src.services.commercial_service import CommercialService, agreement_as_of, fee_percent_for
from apps.api.src.services.errors import ConflictError

NOW = datetime(2030, 6, 1, 12, 0, tzinfo=UTC)


def _harness():
    agreements = InMemoryCommercialAgreementRepository()
    subscriptions = InMemorySubscriptionChargeRepository()
    boosts = InMemoryShiftBoostRepository()
    organisations = InMemoryOrganisationRepository()
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    organisations.save_organisation(
        Organisation(
            organisation_id="org-1", name="Group", country="GB", currency="GBP", created_at=NOW
        )
    )
    for venue_id in ("venue-1", "venue-2"):
        organisations.save_venue(
            Venue(
                venue_id=venue_id, organisation_id="org-1", name=venue_id, country="GB",
                currency="GBP", created_at=NOW, market_id="bath-gb",
            )
        )
    service = CommercialService(agreements, subscriptions, boosts, organisations, shifts)
    return service, agreements, subscriptions, boosts, shifts


def test_a_default_classic_agreement_applies_without_any_row():
    _, agreements, *_ = _harness()
    agreement = agreement_as_of(agreements, "org-1", "GBP", NOW)
    assert agreement.plan == "classic"
    assert agreement.monthly_fee_per_site == Decimal("0.00")


def test_fee_percent_follows_plan_and_basis():
    _, agreements, *_ = _harness()
    classic = agreement_as_of(agreements, "org-1", "GBP", NOW)
    assert fee_percent_for(classic, "venue_employed") == Decimal("0.00")
    assert fee_percent_for(classic, "organisation_employed") == Decimal("0.00")
    assert fee_percent_for(classic, "venue_pool") == classic.outside_fee_percent
    assert fee_percent_for(classic, "outside") == classic.outside_fee_percent


def test_switching_to_plus_zero_rates_the_own_pool_from_the_switch():
    service, agreements, *_ = _harness()
    plus = service.change_plan("org-1", "plus", "user-1", NOW)
    assert plus.plan == "plus"
    assert plus.monthly_fee_per_site == Decimal("25.00")
    assert fee_percent_for(plus, "venue_pool") == Decimal("0.00")
    assert fee_percent_for(plus, "outside") == plus.outside_fee_percent

    before = agreement_as_of(agreements, "org-1", "GBP", NOW - timedelta(days=1))
    assert before.plan == "classic"
    after = agreement_as_of(agreements, "org-1", "GBP", NOW + timedelta(days=1))
    assert after.plan == "plus"


def test_enterprise_cannot_be_self_served():
    service, *_ = _harness()
    from apps.api.src.services.errors import ValidationError

    with pytest.raises(ValidationError):
        service.change_plan("org-1", "enterprise", "user-1", NOW)


def test_subscription_minting_is_per_site_and_idempotent():
    service, agreements, subscriptions, *_ = _harness()
    service.change_plan("org-1", "plus", "user-1", NOW)

    first = service.mint_subscriptions("org-1", "2030-06", NOW)
    assert first == 2
    again = service.mint_subscriptions("org-1", "2030-06", NOW)
    assert again == 0

    rows = subscriptions.list_for_organisation_period("org-1", "2030-06")
    assert {row.venue_id for row in rows} == {"venue-1", "venue-2"}
    assert all(row.amount == Decimal("25.00") for row in rows)


def test_classic_mints_no_subscription():
    service, *_ = _harness()
    assert service.mint_subscriptions("org-1", "2030-06", NOW) == 0


def test_a_shift_holds_at_most_one_active_boost():
    service, agreements, subscriptions, boosts, shifts = _harness()
    from apps.api.src.models.shift import Shift

    shifts.save(
        Shift(
            shift_id="shift-1", operator_id="op-1", account_id="venue-1", role="Bartender",
            location="Bar", start_time=NOW + timedelta(days=3), end_time=NOW + timedelta(days=3, hours=5),
            pay_rate=Decimal("14.00"), notes=None, status="open", created_at=NOW,
            workers_needed=1, currency="GBP",
        )
    )
    boost = service.purchase_boost("shift-1", "venue-1", "top5", "user-1", NOW)
    assert boost.tier == "top5"
    assert boost.price == Decimal("8.00")
    with pytest.raises(ConflictError):
        service.purchase_boost("shift-1", "venue-1", "top1", "user-1", NOW)
