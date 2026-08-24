from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.src.deps import get_organisation_repo, get_report_repo
from apps.api.src.main import app
from apps.api.src.models.organisation import Organisation, Venue
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_report_repository import InMemoryReportRepository


def test_report_submission_status_and_system_review() -> None:
    reports = InMemoryReportRepository()
    organisations = InMemoryOrganisationRepository()
    now = datetime(2030, 1, 1, tzinfo=UTC)
    organisations.save_organisation(
        Organisation("org-1", "Bath Group", "GB", "GBP", now)
    )
    organisations.save_venue(
        Venue("venue-1", "org-1", "Bath Tavern", "GB", "GBP", now)
    )
    app.dependency_overrides[get_report_repo] = lambda: reports
    app.dependency_overrides[get_organisation_repo] = lambda: organisations
    client = TestClient(app)

    created = client.post(
        "/reports",
        json={
            "subject_type": "venue",
            "subject_id": "venue-1",
            "category": "safety",
            "description": "Unsafe working conditions behind the bar.",
        },
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-user-1"},
    )
    assert created.status_code == 201, created.text
    report_id = created.json()["report_id"]

    mine = client.get(
        "/reports/me",
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-user-1"},
    )
    assert [item["report_id"] for item in mine.json()] == [report_id]

    reviewed = client.patch(
        f"/system/reports/{report_id}",
        json={"status": "reviewing", "resolution_notes": "Support is investigating."},
        headers={"X-Actor-Role": "system", "X-Actor-Id": "support-1"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "reviewing"


def test_report_rejects_unknown_subject() -> None:
    app.dependency_overrides[get_report_repo] = lambda: InMemoryReportRepository()
    app.dependency_overrides[get_organisation_repo] = lambda: InMemoryOrganisationRepository()
    client = TestClient(app)

    response = client.post(
        "/reports",
        json={
            "subject_type": "venue",
            "subject_id": "missing",
            "category": "other",
            "description": "This venue reference should not be accepted.",
        },
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-user-1"},
    )

    assert response.status_code == 404
