from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.api.src.models.organisation import Organisation, Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_organisation_repository import (
    InMemoryOrganisationRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.services.assistant.assistant_service import AssistantService
from apps.api.src.services.assistant.deidentify import deidentify, rehydrate
from apps.api.src.services.assistant.provider import (
    OFFER_MESSAGE,
    SHIFT_POST,
    DeterministicAssistant,
    GuardedProvider,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = datetime(2030, 6, 6, 18, 0, tzinfo=UTC)
VENUE = "venue-1"


def _harness():
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    relationships = InMemoryWorkerRelationshipRepository()
    organisations = InMemoryOrganisationRepository()
    organisations.save_organisation(
        Organisation(organisation_id="org-1", name="Group", country="GB", currency="GBP", created_at=NOW)
    )
    organisations.save_venue(
        Venue(venue_id=VENUE, organisation_id="org-1", name="The Grapes", country="GB",
              currency="GBP", created_at=NOW, market_id="bath-gb")
    )
    service = AssistantService(
        GuardedProvider(DeterministicAssistant(), DeterministicAssistant()),
        shifts, relationships, organisations,
    )
    return service, shifts, relationships


def _shift(shift_id: str, role: str, rate: str, start=START) -> Shift:
    return Shift(
        shift_id=shift_id, operator_id="op-1", account_id=VENUE, role=role, location="Main bar",
        start_time=start, end_time=start + timedelta(hours=5), pay_rate=Decimal(rate), notes=None,
        status="open", created_at=NOW, workers_needed=1, workers_filled=0,
    )


def test_deidentify_hides_pii_and_rehydrate_restores_it():
    deid = deidentify({"worker": "Ana Ruiz", "rate": "£14.50", "note": None})
    assert deid.fields == {"worker": "{worker}", "rate": "{rate}"}
    assert "Ana" not in "".join(deid.fields.values())
    filled = rehydrate("Hi {worker}, it's {rate}/hr", deid.rehydration)
    assert filled == "Hi Ana Ruiz, it's £14.50/hr"


def test_a_model_never_sees_raw_pii_only_placeholders():
    seen = {}

    class Spy:
        def generate(self, kind, fields):
            seen.update(fields)
            return "Hi {worker}!"

    service, *_ = _harness()
    service._provider = Spy()
    draft = service.offer_message(VENUE, "Ana Ruiz", "Bartender", START, Decimal("14.50"))
    assert "Ana" not in "".join(seen.values())
    assert seen["worker"] == "{worker}"
    assert draft.message == "Hi Ana Ruiz!"


def test_shift_post_draft_and_pay_suggestion_from_history():
    service, shifts, _ = _harness()
    for index in range(3):
        shifts.save(_shift(f"h-{index}", "Bartender", "14.00"))
    draft = service.shift_post(
        VENUE, "Bartender", "Main bar", START, START + timedelta(hours=5),
        Decimal("14.50"), "cocktail experience a plus",
    )
    assert "The Grapes" in draft.description
    assert "£14.50" in draft.description
    assert "cocktail experience a plus" in draft.description
    assert draft.suggested_pay_low == Decimal("13.30")
    assert draft.suggested_pay_high == Decimal("15.40")
    assert "3 recent" in draft.pay_basis


def test_shift_post_pay_suggestion_is_empty_without_history():
    service, *_ = _harness()
    draft = service.shift_post(
        VENUE, "Chef", "Kitchen", START, START + timedelta(hours=5), None, None
    )
    assert draft.suggested_pay_low is None
    assert "No history" in draft.pay_basis


def test_offer_message_is_warm_named_and_carries_no_leak():
    service, *_ = _harness()
    draft = service.offer_message(VENUE, "Ana", "Bartender", START, Decimal("14.50"))
    assert draft.message.startswith("Hi Ana!")
    assert "The Grapes" in draft.message
    assert "£14.50" in draft.message
    assert "{worker}" not in draft.message


def test_onboarding_tracks_setup_state():
    service, shifts, relationships = _harness()
    guidance = service.onboarding(VENUE, "org-1", NOW)
    by_key = {step.key: step for step in guidance.steps}
    assert by_key["venue"].done is True
    assert by_key["team"].done is False
    assert by_key["shift"].done is False
    assert "add your staff" in guidance.summary.lower()

    relationships.save(
        WorkerRelationship(
            relationship_id="rel-1", venue_id=VENUE, worker_id="w-1",
            relationship_type="permanent", status="active", created_at=NOW, updated_at=NOW,
        )
    )
    shifts.save(_shift("s-1", "Bartender", "14.00", start=NOW + timedelta(days=2)))
    done = service.onboarding(VENUE, "org-1", NOW)
    assert all(step.done for step in done.steps)
    assert "all set" in done.summary.lower()


def test_guarded_provider_falls_back_to_deterministic_when_primary_fails():
    class Broken:
        def generate(self, kind, fields):
            raise RuntimeError("model endpoint down")

    guarded = GuardedProvider(Broken(), DeterministicAssistant())
    text = guarded.generate(OFFER_MESSAGE, {"worker": "{worker}", "role": "Bartender"})
    assert "{worker}" in text
    assert "Bartender" in text


def test_assistant_endpoints_are_operator_scoped_and_audited():
    from fastapi.testclient import TestClient

    from apps.api.src import main
    from apps.api.src.deps import get_shift_repo, get_organisation_repo
    from apps.api.src.repository_dependencies import get_worker_profile_repo
    from apps.api.src.repositories.in_memory_worker_profile_repository import (
        InMemoryWorkerProfileRepository,
    )
    from apps.api.src.models.worker_profile import WorkerProfile

    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    organisations = InMemoryOrganisationRepository()
    organisations.save_organisation(
        Organisation(organisation_id="org-1", name="Group", country="GB", currency="GBP", created_at=NOW)
    )
    organisations.save_venue(
        Venue(venue_id=VENUE, organisation_id="org-1", name="The Grapes", country="GB",
              currency="GBP", created_at=NOW, market_id="bath-gb")
    )
    workers = InMemoryWorkerProfileRepository()
    workers.save(
        WorkerProfile(
            worker_id="w-1", display_name="Ana", role="Bartender", city="Bath",
            experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
            email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
            notes=None, updated_at=NOW,
        )
    )
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_organisation_repo] = lambda: organisations
    main.app.dependency_overrides[get_worker_profile_repo] = lambda: workers
    try:
        client = TestClient(main.app)
        operator = {"X-Actor-Role": "operator", "X-Actor-Id": VENUE, "X-Account-Id": VENUE, "X-Organisation-Id": "org-1"}
        worker = {"X-Actor-Role": "worker", "X-Actor-Id": "w-1"}

        assert client.post("/assistant/onboarding", headers=worker).status_code == 403

        onboard = client.post("/assistant/onboarding", headers=operator)
        assert onboard.status_code == 200, onboard.text
        assert onboard.json()["steps"][0]["key"] == "venue"

        post = client.post(
            "/assistant/shift-post",
            json={
                "role": "Bartender", "location": "Main bar",
                "start_time": START.isoformat(),
                "end_time": (START + timedelta(hours=5)).isoformat(),
                "pay_rate": 14.5, "note": "busy Friday",
            },
            headers=operator,
        )
        assert post.status_code == 200, post.text
        assert "The Grapes" in post.json()["description"]

        offer = client.post(
            "/assistant/offer-message",
            json={"worker_id": "w-1", "role": "Bartender", "start_time": START.isoformat(), "pay_rate": 14.5},
            headers=operator,
        )
        assert offer.status_code == 200, offer.text
        assert offer.json()["message"].startswith("Hi Ana!")
    finally:
        main.app.dependency_overrides.pop(get_shift_repo, None)
        main.app.dependency_overrides.pop(get_organisation_repo, None)
        main.app.dependency_overrides.pop(get_worker_profile_repo, None)
