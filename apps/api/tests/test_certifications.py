from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_certification import (
    WorkerCertification,
    normalize_certification_name,
)
from apps.api.src.repositories.in_memory_worker_certification_repository import (
    InMemoryWorkerCertificationRepository,
)
from apps.api.src.repository_dependencies import shared_worker_certification_repository
from apps.api.src.services.certification_expiry import sweep_certification_expiry
from apps.api.src.services.certification_gate import CertificationGate, MissingCertificationError

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_worker_certification_repository().clear()
    yield
    shared_worker_certification_repository().clear()


def _shift(**overrides) -> Shift:
    values = dict(
        shift_id="shift-1",
        operator_id="operator-1",
        account_id="venue-1",
        role="Bartender",
        location="Main bar",
        start_time=START,
        end_time=START + timedelta(hours=5),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="open",
        created_at=NOW,
        workers_needed=1,
        required_certification="Personal Licence",
    )
    values.update(overrides)
    return Shift(**values)


def _certification(expires_at: datetime, name: str = "personal licence") -> WorkerCertification:
    return WorkerCertification(
        certification_id=f"cert-{name}",
        worker_id="worker-1",
        name=name,
        display_name="Personal Licence",
        expires_at=expires_at,
        created_at=NOW,
        updated_at=NOW,
    )


def test_the_gate_only_blocks_shifts_that_require_a_certification():
    repo = InMemoryWorkerCertificationRepository()
    gate = CertificationGate(repo)
    gate.ensure_certified("worker-1", _shift(required_certification=None))
    with pytest.raises(MissingCertificationError):
        gate.ensure_certified("worker-1", _shift())


def test_a_certification_must_be_current_at_shift_start_not_today():
    repo = InMemoryWorkerCertificationRepository()
    gate = CertificationGate(repo)
    repo.save(_certification(expires_at=START - timedelta(days=1)))
    with pytest.raises(MissingCertificationError):
        gate.ensure_certified("worker-1", _shift())

    repo.save(_certification(expires_at=START + timedelta(days=1)))
    gate.ensure_certified("worker-1", _shift())


def test_certification_names_match_after_normalization():
    repo = InMemoryWorkerCertificationRepository()
    gate = CertificationGate(repo)
    repo.save(_certification(expires_at=START + timedelta(days=30)))
    gate.ensure_certified("worker-1", _shift(required_certification="  PERSONAL   licence "))


def test_normalization_collapses_case_and_spacing():
    assert normalize_certification_name("  Personal   LICENCE ") == "personal licence"


def test_a_worker_manages_their_certifications_over_the_api():
    client = TestClient(main.app)
    response = client.put(
        "/me/certifications/Personal Licence",
        json={"display_name": "Personal Licence", "expires_at": "2031-01-01T00:00:00Z"},
        headers=WORKER,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "personal licence"

    response = client.put(
        "/me/certifications/personal   LICENCE",
        json={
            "display_name": "Personal Licence",
            "expires_at": "2032-01-01T00:00:00Z",
            "reference": "PL-1234",
        },
        headers=WORKER,
    )
    assert response.status_code == 200
    assert response.json()["certification_id"] == body["certification_id"]

    listed = client.get("/me/certifications", headers=WORKER).json()
    assert [item["reference"] for item in listed] == ["PL-1234"]
    assert client.get("/me/certifications", headers=OTHER_WORKER).json() == []

    assert client.delete("/me/certifications/Personal Licence", headers=WORKER).status_code == 204
    assert client.get("/me/certifications", headers=WORKER).json() == []
    assert client.delete("/me/certifications/Personal Licence", headers=WORKER).status_code == 404


class RecordingOutbox:
    def __init__(self) -> None:
        self.notifications = []

    def publish_notification(self, **kwargs) -> None:
        self.notifications.append(kwargs)


def test_the_expiry_sweep_stages_notices_by_time_left():
    repo = InMemoryWorkerCertificationRepository()
    outbox = RecordingOutbox()
    repo.save(_certification(NOW - timedelta(days=2), name="expired cert"))
    repo.save(_certification(NOW + timedelta(days=3), name="soon cert"))
    repo.save(_certification(NOW + timedelta(days=20), name="later cert"))
    repo.save(_certification(NOW + timedelta(days=200), name="fine cert"))

    published = sweep_certification_expiry(repo, outbox, NOW)

    events = {n["aggregate_id"]: n["event_type"] for n in outbox.notifications}
    assert published == 3
    assert events == {
        "cert-expired cert": "certification.expired",
        "cert-soon cert": "certification.expiring_7d",
        "cert-later cert": "certification.expiring_30d",
    }
    again = sweep_certification_expiry(repo, outbox, NOW)
    assert again == 3
    assert {n["aggregate_id"] for n in outbox.notifications} == set(events)


def _application_service(certifications: InMemoryWorkerCertificationRepository):
    from apps.api.src.repositories.in_memory_application_decision_repository import (
        InMemoryApplicationDecisionRepository,
    )
    from apps.api.src.repositories.in_memory_application_message_history_repository import (
        InMemoryApplicationMessageHistoryRepository,
    )
    from apps.api.src.repositories.in_memory_application_repository import (
        InMemoryApplicationRepository,
    )
    from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
    from apps.api.src.repositories.in_memory_notification_repository import (
        InMemoryNotificationRepository,
    )
    from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
    from apps.api.src.repositories.in_memory_worker_relationship_repository import (
        InMemoryWorkerRelationshipRepository,
    )
    from apps.api.src.services.application_service import ApplicationService
    from apps.api.src.services.email import LoggingEmailTransport
    from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher

    applications = InMemoryApplicationRepository()
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    applications.attach_shift_repo(shifts)
    bookings.attach_shift_repo(shifts)
    service = ApplicationService(
        applications,
        shifts,
        InMemoryApplicationDecisionRepository(applications, bookings, shifts),
        InMemoryApplicationMessageHistoryRepository(),
        InMemoryOutboxPublisher(InMemoryNotificationRepository(), LoggingEmailTransport()),
        InMemoryWorkerRelationshipRepository(),
        CertificationGate(certifications),
    )
    return service, shifts


def test_applying_requires_the_shifts_certification():
    from apps.api.src.schemas import ApplicationCreateRequest
    from apps.api.src.services.errors import ValidationError

    certifications = InMemoryWorkerCertificationRepository()
    service, shifts = _application_service(certifications)
    shifts.save(_shift(account_id=None, origin="market"))

    request = ApplicationCreateRequest(shift_id="shift-1", worker_id="worker-1", now=NOW)
    with pytest.raises(ValidationError):
        service.create_application(request)

    certifications.save(_certification(START + timedelta(days=10)))
    created = service.create_application(request)
    assert created.status == "applied"


def test_approval_rechecks_a_certification_that_lapsed_after_applying():
    from apps.api.src.schemas import ApplicationCreateRequest, ApplicationDecisionRequest
    from apps.api.src.services.errors import ValidationError

    certifications = InMemoryWorkerCertificationRepository()
    service, shifts = _application_service(certifications)
    shifts.save(_shift(account_id=None, origin="market"))
    certifications.save(_certification(START + timedelta(days=10)))
    created = service.create_application(
        ApplicationCreateRequest(shift_id="shift-1", worker_id="worker-1", now=NOW)
    )

    certifications.save(_certification(START - timedelta(days=1)))
    with pytest.raises(ValidationError):
        service.approve_application(created.application_id, ApplicationDecisionRequest(now=NOW))

    certifications.save(_certification(START + timedelta(days=10)))
    approved = service.approve_application(created.application_id, ApplicationDecisionRequest(now=NOW))
    assert approved.status == "approved"
