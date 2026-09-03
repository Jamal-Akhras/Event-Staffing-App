from datetime import UTC, datetime, timedelta

import pytest

from apps.api.src.services.escalation_policy import (
    EscalationPolicy,
    plan_rungs,
    policy_from_venue,
)

START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)
NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)

LEGACY = EscalationPolicy(named_offer_hours=24, team_hours=None, pool_hours=24, market_lead_hours=48)


def test_a_missing_policy_reads_as_the_defaults():
    policy = policy_from_venue(None)
    assert policy == EscalationPolicy(24, None, 24, 48)


def test_a_stored_policy_requires_all_four_keys():
    with pytest.raises(ValueError, match="missing"):
        policy_from_venue({"pool_hours": 24, "market_lead_hours": 48})
    with pytest.raises(ValueError, match="negative"):
        policy_from_venue(
            {"named_offer_hours": -1, "team_hours": None, "pool_hours": 24, "market_lead_hours": 48}
        )
    policy = policy_from_venue(
        {"named_offer_hours": 12, "team_hours": 6, "pool_hours": 24, "market_lead_hours": 48}
    )
    assert (policy.named_offer_hours, policy.team_hours) == (12, 6)


def test_an_assigned_shift_under_a_legacy_policy_keeps_its_old_stamps():
    stamps = plan_rungs(START, NOW, LEGACY, "assigned", has_team=False, has_pool=True)
    assert stamps.offer_team_at is None
    assert stamps.offer_pool_at == NOW + timedelta(hours=24)
    assert stamps.publish_market_at == NOW + timedelta(hours=48)


def test_an_unassigned_pool_start_keeps_its_old_stamps():
    stamps = plan_rungs(START, NOW, LEGACY, "pool", has_team=False, has_pool=True)
    assert stamps.offer_pool_at == NOW
    assert stamps.publish_market_at == NOW + timedelta(hours=24)


def test_the_team_rung_slots_between_the_named_hold_and_the_pool():
    policy = EscalationPolicy(named_offer_hours=12, team_hours=6, pool_hours=24, market_lead_hours=48)
    stamps = plan_rungs(START, NOW, policy, "assigned", has_team=True, has_pool=True)
    assert stamps.offer_team_at == NOW + timedelta(hours=12)
    assert stamps.offer_pool_at == NOW + timedelta(hours=18)
    assert stamps.publish_market_at == NOW + timedelta(hours=42)


def test_an_empty_team_audience_consumes_no_time():
    policy = EscalationPolicy(named_offer_hours=12, team_hours=6, pool_hours=24, market_lead_hours=48)
    stamps = plan_rungs(START, NOW, policy, "assigned", has_team=False, has_pool=True)
    assert stamps.offer_team_at is None
    assert stamps.offer_pool_at == NOW + timedelta(hours=12)


def test_the_market_deadline_wins_over_slow_private_windows():
    late = START - timedelta(hours=10)
    stamps = plan_rungs(START, late, LEGACY, "assigned", has_team=False, has_pool=True)
    assert stamps.publish_market_at == max(START - timedelta(hours=48), stamps.offer_pool_at)


def test_a_null_named_hold_waits_for_an_explicit_answer():
    policy = EscalationPolicy(named_offer_hours=None, team_hours=6, pool_hours=24, market_lead_hours=48)
    stamps = plan_rungs(START, NOW, policy, "assigned", has_team=True, has_pool=True)
    assert stamps == plan_rungs(START, NOW, policy, "assigned", True, True)
    assert (stamps.offer_team_at, stamps.offer_pool_at, stamps.publish_market_at) == (None, None, None)


def test_a_market_start_publishes_at_once():
    stamps = plan_rungs(START, NOW, LEGACY, "market", has_team=False, has_pool=False)
    assert stamps.publish_market_at == NOW
    assert stamps.offer_team_at is None and stamps.offer_pool_at is None
