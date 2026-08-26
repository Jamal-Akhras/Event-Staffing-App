from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_booking_repo, get_worker_profile_repo
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)
from packages.domain.src.booking import Booking

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}
SYSTEM_HEADERS = {"X-Actor-Role": "system", "X-Actor-Id": "system"}


def _client() -> TestClient:
    booking_repo = InMemoryBookingRepository()
    profile_repo = InMemoryWorkerProfileRepository()
    main.app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    main.app.dependency_overrides[get_worker_profile_repo] = lambda: profile_repo
    return TestClient(main.app)


def _create_profile(client: TestClient, worker_id: str, now: datetime) -> None:
    response = client.put(
        f"/workers/{worker_id}",
        json={
            "display_name": "Alex Worker",
            "role": "server",
            "city": "Austin",
            "experience_years": 3,
            "bio": "Reliable and punctual.",
            "languages": ["en"],
            "email": "alex@example.com",
            "phone": "555-0100",
            "address": "100 Main St",
            "emergency_contact": "555-0101",
            "pay_rate": 25.0,
            "notes": "Prefers evening shifts.",
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id},
    )
    assert response.status_code == 200


def _create_booking(
    client: TestClient,
    worker_id: str,
    now: datetime,
    start_offset_minutes: int,
) -> str:
    start = now + timedelta(minutes=start_offset_minutes)
    end = start + timedelta(hours=4)
    booking_id = str(uuid4())
    repo = main.app.dependency_overrides[get_booking_repo]()
    repo.save(
        Booking(
            booking_id=booking_id,
            shift_id="shift-1",
            worker_id=worker_id,
            operator_id="operator-1",
            start_time=start,
            end_time=end,
            created_at=now,
        )
    )
    return booking_id


def test_reliability_updates_from_outcomes():
    client = _client()
    base = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    worker_id = "worker-1"
    _create_profile(client, worker_id, base)

    booking_one = _create_booking(client, worker_id, base, start_offset_minutes=60)
    client.post(
        f"/bookings/{booking_one}/confirm",
        json={"now": (base + timedelta(minutes=5)).isoformat()},
        headers=OPERATOR_HEADERS,
    )
    check_in_time = base + timedelta(minutes=40)
    check_in_code = main.app.dependency_overrides[get_booking_repo]().get(booking_one).check_in_code
    client.post(
        f"/bookings/{booking_one}/check-in",
        json={"now": check_in_time.isoformat(), "code": check_in_code},
        headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id},
    )
    check_out = client.post(
        f"/bookings/{booking_one}/check-out",
        json={"now": (check_in_time + timedelta(hours=4)).isoformat()},
        headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id},
    )
    assert check_out.status_code == 200

    booking_two = _create_booking(client, worker_id, base, start_offset_minutes=10)
    client.post(
        f"/bookings/{booking_two}/confirm",
        json={"now": (base + timedelta(minutes=1)).isoformat()},
        headers=OPERATOR_HEADERS,
    )
    no_show = client.post(
        f"/bookings/{booking_two}/no-show",
        json={"now": (base + timedelta(minutes=30)).isoformat()},
        headers=OPERATOR_HEADERS,
    )
    assert no_show.status_code == 200

    profile = client.get(f"/workers/{worker_id}", headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id})
    assert profile.status_code == 200
    assert profile.json()["reliability_score"] == 0.5


def test_no_show_sweep_marks_expired_bookings():
    client = _client()
    base = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    worker_id = "worker-2"
    _create_profile(client, worker_id, base)

    start = base - timedelta(hours=1)
    end = start + timedelta(hours=4)
    booking_id = str(uuid4())
    repo = main.app.dependency_overrides[get_booking_repo]()
    repo.save(
        Booking(
            booking_id=booking_id,
            shift_id="shift-2",
            worker_id=worker_id,
            operator_id="operator-1",
            start_time=start,
            end_time=end,
            created_at=base - timedelta(hours=2),
        )
    )
    client.post(
        f"/bookings/{booking_id}/confirm",
        json={"now": (base - timedelta(hours=1, minutes=50)).isoformat()},
        headers=OPERATOR_HEADERS,
    )

    sweep = client.post(
        "/system/no-show-sweep",
        json={"now": base.isoformat()},
        headers=SYSTEM_HEADERS,
    )
    assert sweep.status_code == 200
    assert sweep.json()[0]["state"] == "no_show"

    profile = client.get(f"/workers/{worker_id}", headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id})
    assert profile.status_code == 200
    assert profile.json()["reliability_score"] == 0.0
