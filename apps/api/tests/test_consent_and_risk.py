from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.consent import PURPOSE_PRIVACY, PURPOSE_PROFILING, PURPOSE_TERMS
from apps.api.src.repositories.in_memory_consent_repository import InMemoryConsentRepository
from apps.api.src.repository_dependencies import shared_consent_repository
from apps.api.src.services.consent_service import ConsentService

NOW = datetime(2030, 6, 1, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def clear_state():
    shared_consent_repository().clear()
    yield
    shared_consent_repository().clear()


def test_registration_records_terms_and_privacy_as_acknowledgements():
    repo = InMemoryConsentRepository()
    service = ConsentService(repo)
    service.record_registration("user-1", NOW)

    events = repo.list_for_user("user-1")
    by_purpose = {event.purpose: event for event in events}
    assert by_purpose[PURPOSE_TERMS].action == "acknowledged"
    assert by_purpose[PURPOSE_PRIVACY].action == "acknowledged"
    assert by_purpose[PURPOSE_TERMS].basis == "contract"
    assert service.has_active_consent("user-1", PURPOSE_TERMS) is False


def test_profiling_consent_is_grantable_and_withdrawable_as_immutable_events():
    repo = InMemoryConsentRepository()
    service = ConsentService(repo)

    assert service.has_active_consent("user-1", PURPOSE_PROFILING) is False
    service.set_profiling("user-1", True, NOW)
    assert service.has_active_consent("user-1", PURPOSE_PROFILING) is True
    service.set_profiling("user-1", False, NOW + timedelta(hours=1))
    assert service.has_active_consent("user-1", PURPOSE_PROFILING) is False

    events = repo.list_for_user("user-1")
    assert [event.action for event in events] == ["granted", "withdrawn"]
    assert service.current_state("user-1")[PURPOSE_PROFILING] == "withdrawn"


def _worker_client():
    client = TestClient(main.app)
    email = f"consent-{int(utc_now().timestamp() * 1000)}@example.com"
    registered = client.post("/auth/register", json={"email": email, "password": "consent-pass-1"})
    assert registered.status_code == 200, registered.text
    token = registered.json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


def test_the_worker_can_read_and_change_profiling_consent_over_the_api():
    client, headers = _worker_client()

    state = client.get("/me/consents", headers=headers)
    assert state.status_code == 200, state.text
    assert state.json()["consents"].get(PURPOSE_TERMS) == "acknowledged"
    assert state.json()["consents"].get(PURPOSE_PRIVACY) == "acknowledged"

    granted = client.put("/me/consents/profiling", json={"granted": True}, headers=headers)
    assert granted.status_code == 200, granted.text
    assert granted.json()["consents"][PURPOSE_PROFILING] == "granted"

    withdrawn = client.put("/me/consents/profiling", json={"granted": False}, headers=headers)
    assert withdrawn.json()["consents"][PURPOSE_PROFILING] == "withdrawn"


def test_risk_information_flows_through_create_update_and_response():
    from apps.api.src.deps import get_shift_repo, get_account_repo
    from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
    from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository

    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    try:
        client = TestClient(main.app)
        start = (utc_now() + timedelta(days=3)).replace(microsecond=0)
        created = client.post(
            "/shifts",
            json={
                "role": "Bartender",
                "location": "Cellar bar",
                "start_time": start.isoformat(),
                "end_time": (start + timedelta(hours=5)).isoformat(),
                "pay_rate": 14.0,
                "workers_needed": 1,
                "risk_information": "Low ceilings and wet floors in the cellar.",
            },
            headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Actor-Verified": "true"},
        )
        assert created.status_code == 200, created.text
        assert created.json()["risk_information"] == "Low ceilings and wet floors in the cellar."

        fetched = client.get(
            f"/shifts/{created.json()['shift_id']}",
            headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"},
        )
        assert fetched.json()["risk_information"] == "Low ceilings and wet floors in the cellar."
    finally:
        main.app.dependency_overrides.pop(get_shift_repo, None)
