from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_booking_repo
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from packages.domain.src.booking import Booking

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}
OTHER_OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2"}
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}
SYSTEM_HEADERS = {"X-Actor-Role": "system", "X-Actor-Id": "system"}


def _client() -> TestClient:
    from apps.api.src.deps import get_shift_repo
    from apps.api.src.models.shift import Shift
    from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
    repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(repo)
    repo.attach_shift_repo(shift_repo)
    now = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    shift_repo.save(
        Shift(
            shift_id="shift-1",
            operator_id="operator-1",
            account_id="operator-1",
            role="server",
            location="Downtown",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=5),
            pay_rate=25.0,
            notes=None,
            status="open",
            created_at=now,
            workers_needed=1,
            workers_filled=0,
        )
    )
    main.app.dependency_overrides[get_booking_repo] = lambda: repo
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    return TestClient(main.app)


def _create_booking(client: TestClient, start_offset_minutes: int = 60) -> tuple[str, datetime]:
    now = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    start = now + timedelta(minutes=start_offset_minutes)
    end = start + timedelta(hours=4)
    booking_id = str(uuid4())
    repo = main.app.dependency_overrides[get_booking_repo]()
    repo.save(
        Booking(
            booking_id=booking_id,
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=start,
            end_time=end,
            created_at=now,
        )
    )
    return booking_id, now


def test_direct_booking_creation_is_not_exposed():
    client = _client()
    response = client.post("/bookings", json={}, headers=OPERATOR_HEADERS)
    assert response.status_code == 405


def test_booking_lifecycle_happy_path():
    client = _client()
    booking_id, now = _create_booking(client)

    confirm = client.post(
        f"/bookings/{booking_id}/confirm",
        json={"now": (now + timedelta(minutes=5)).isoformat()},
        headers=OPERATOR_HEADERS,
    )
    assert confirm.status_code == 200
    assert confirm.json()["state"] == "confirmed"

    booking = main.app.dependency_overrides[get_booking_repo]().get(booking_id)
    assert confirm.json()["check_in_code"] == booking.check_in_code
    assert confirm.json()["completion_code"] is None

    check_in_time = now + timedelta(minutes=40)
    wrong_code = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": check_in_time.isoformat(), "code": "0000" if booking.check_in_code != "0000" else "0001"},
        headers=WORKER_HEADERS,
    )
    assert wrong_code.status_code == 400
    assert "check-in code" in wrong_code.json()["detail"]
    check_in = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": check_in_time.isoformat(), "code": booking.check_in_code},
        headers=WORKER_HEADERS,
    )
    assert check_in.status_code == 200
    assert check_in.json()["state"] == "checked_in"
    assert check_in.json()["completion_code"] == booking.completion_code
    assert check_in.json()["check_in_code"] is None
    assert client.get(f"/bookings/{booking_id}", headers=OPERATOR_HEADERS).json()["check_in_code"] is None

    check_out = client.post(
        f"/bookings/{booking_id}/check-out",
        json={"now": (check_in_time + timedelta(hours=4)).isoformat()},
        headers=WORKER_HEADERS,
    )
    assert check_out.status_code == 200
    assert check_out.json()["state"] == "checked_out"

    missing_code = client.post(
        f"/bookings/{booking_id}/approve",
        json={"now": (now + timedelta(hours=5)).isoformat()},
        headers=OPERATOR_HEADERS,
    )
    assert missing_code.status_code == 400
    approve = client.post(
        f"/bookings/{booking_id}/approve",
        json={"now": (now + timedelta(hours=5)).isoformat(), "code": booking.completion_code},
        headers=OPERATOR_HEADERS,
    )
    assert approve.status_code == 200
    assert approve.json()["state"] == "approved"
    assert client.get(f"/bookings/{booking_id}", headers=WORKER_HEADERS).json()["completion_code"] is None

    pay = client.post(
        f"/bookings/{booking_id}/pay",
        json={
            "confirmation": "PAYMENT_SENT",
            "method": "bank_transfer",
            "reference": "BACS-123",
            "now": (now + timedelta(hours=6)).isoformat(),
        },
        headers=OPERATOR_HEADERS,
    )
    assert pay.status_code == 200
    assert pay.json()["state"] == "paid"
    assert pay.json()["payment_method"] == "bank_transfer"
    assert pay.json()["payment_reference"] == "BACS-123"


def test_invalid_transition_returns_400():
    client = _client()
    booking_id, now = _create_booking(client)

    check_in = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (now + timedelta(minutes=10)).isoformat()},
        headers=WORKER_HEADERS,
    )
    assert check_in.status_code == 400


def test_check_in_code_attempts_are_rate_limited():
    client = _client()
    booking_id, now = _create_booking(client)
    booking = main.app.dependency_overrides[get_booking_repo]().get(booking_id)
    wrong_code = "0000" if booking.check_in_code != "0000" else "0001"

    for _ in range(5):
        response = client.post(
            f"/bookings/{booking_id}/check-in",
            json={"now": (now + timedelta(minutes=40)).isoformat(), "code": wrong_code},
            headers=WORKER_HEADERS,
        )
        assert response.status_code == 400

    limited = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (now + timedelta(minutes=40)).isoformat(), "code": wrong_code},
        headers=WORKER_HEADERS,
    )
    assert limited.status_code == 429


def test_no_show_requires_window_closed():
    client = _client()
    booking_id, now = _create_booking(client)
    client.post(
        f"/bookings/{booking_id}/confirm",
        json={"now": (now + timedelta(minutes=5)).isoformat()},
        headers=OPERATOR_HEADERS,
    )

    too_early = now + timedelta(minutes=70)
    response = client.post(
        f"/bookings/{booking_id}/no-show",
        json={"now": too_early.isoformat()},
        headers=OPERATOR_HEADERS,
    )
    assert response.status_code == 400

    after_close = now + timedelta(minutes=76)
    response = client.post(
        f"/bookings/{booking_id}/no-show",
        json={"now": after_close.isoformat()},
        headers=OPERATOR_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["state"] == "no_show"


def test_list_bookings_returns_recent():
    client = _client()
    booking_id, _ = _create_booking(client)
    response = client.get("/bookings", headers=OPERATOR_HEADERS)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["booking_id"] == booking_id


def test_role_required():
    client = _client()
    response = client.get("/bookings")
    assert response.status_code == 401


def test_booking_access_is_limited_to_owner():
    client = _client()
    booking_id, now = _create_booking(client)

    other_operator = client.get(f"/bookings/{booking_id}", headers=OTHER_OPERATOR_HEADERS)
    assert other_operator.status_code == 403

    other_worker = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (now + timedelta(minutes=40)).isoformat()},
        headers=OTHER_WORKER_HEADERS,
    )
    assert other_worker.status_code == 403
