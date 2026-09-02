from datetime import UTC, datetime, timedelta

import pytest

from apps.api.src.services.escalation_policy import (
    EscalationPolicy,
    next_timestamps,
    policy_from_venue,
)

NOW = datetime(2030, 6, 1, 9, 0, tzinfo=UTC)


def _hours(value: datetime | None) -> float | None:
    return None if value is None else (value - NOW).total_seconds() / 3600


@pytest.mark.parametrize(
    "lead_hours, assigned, expected_pool, expected_market",
    [
        (24 * 30, False, 0, 24),
        (24 * 30, True, 24, 48),
        (72, False, 0, 24),
        (30, False, 0, 0),
        (26, False, 0, 0),
        (10, False, 0, 0),
        (1, False, 0, 0),
    ],
)
def test_the_ladder_takes_whichever_rung_comes_first(lead_hours, assigned, expected_pool, expected_market):
    start = NOW + timedelta(hours=lead_hours)
    stamps = next_timestamps(start, NOW, EscalationPolicy(), assigned)
    assert _hours(stamps.offer_pool_at) == expected_pool
    assert _hours(stamps.publish_market_at) == expected_market


def test_a_long_lead_shift_gives_the_pool_its_full_window():
    start = NOW + timedelta(days=90)
    stamps = next_timestamps(start, NOW, EscalationPolicy(pool_hours=48, market_lead_hours=24), False)
    assert _hours(stamps.publish_market_at) == 48


def test_a_short_lead_shift_reaches_the_market_on_the_deadline_instead():
    start = NOW + timedelta(hours=36)
    stamps = next_timestamps(start, NOW, EscalationPolicy(pool_hours=48, market_lead_hours=24), False)
    assert _hours(stamps.publish_market_at) == 12


def test_a_drop_on_the_day_reaches_the_market_immediately():
    start = NOW + timedelta(hours=2)
    stamps = next_timestamps(start, NOW, EscalationPolicy(), False)
    assert stamps.publish_market_at == NOW


def test_turning_the_market_rung_off_keeps_a_shift_private_forever():
    stamps = next_timestamps(NOW + timedelta(days=5), NOW, EscalationPolicy(market_lead_hours=None), False)
    assert stamps.publish_market_at is None
    assert stamps.offer_pool_at == NOW


def test_turning_the_pool_rung_off_sends_a_shift_straight_to_the_market():
    stamps = next_timestamps(NOW + timedelta(days=5), NOW, EscalationPolicy(pool_hours=None), False)
    assert stamps.offer_pool_at is None
    assert stamps.publish_market_at == NOW


def test_a_venue_with_no_policy_gets_the_defaults():
    assert policy_from_venue(None) == EscalationPolicy()
    assert policy_from_venue({}) == EscalationPolicy()


def test_a_stored_policy_can_switch_a_rung_off():
    policy = policy_from_venue({"pool_hours": 6, "market_lead_hours": None})
    assert (policy.pool_hours, policy.market_lead_hours) == (6, None)
    assert policy.offers_pool is True
    assert policy.reaches_market is False


def test_a_negative_window_is_refused():
    with pytest.raises(ValueError):
        policy_from_venue({"pool_hours": -1})
