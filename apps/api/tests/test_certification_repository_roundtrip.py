from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from apps.api.src.models.worker_certification import WorkerCertification
from apps.api.src.repositories.sqlalchemy_worker_certification_repository import (
    SqlAlchemyWorkerCertificationRepository,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)


def _certification(certification_id: str, **overrides) -> WorkerCertification:
    values = dict(
        certification_id=certification_id,
        worker_id="worker-1",
        name="personal licence",
        display_name="Personal Licence",
        expires_at=NOW + timedelta(days=90),
        reference="PL-1234",
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(overrides)
    return WorkerCertification(**values)


def test_every_certification_field_survives_a_sql_round_trip(repo_session):
    repo = SqlAlchemyWorkerCertificationRepository(repo_session)
    saved = _certification("cert-rt-1")
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    assert repo.get("worker-1", "personal licence") == saved
    assert repo.list_for_worker("worker-1") == [saved]


def test_upsert_replaces_and_delete_removes(repo_session):
    repo = SqlAlchemyWorkerCertificationRepository(repo_session)
    repo.save(_certification("cert-rt-2"))
    repo.save(
        _certification("cert-rt-2", expires_at=NOW + timedelta(days=365), reference=None)
    )

    loaded = repo.get("worker-1", "personal licence")
    assert loaded.expires_at == NOW + timedelta(days=365)
    assert loaded.reference is None

    assert repo.delete("worker-1", "personal licence") is True
    assert repo.delete("worker-1", "personal licence") is False
    assert repo.list_for_worker("worker-1") == []


def test_expiry_window_query_is_half_open(repo_session):
    repo = SqlAlchemyWorkerCertificationRepository(repo_session)
    repo.save(_certification("cert-a", name="cert a", expires_at=NOW + timedelta(days=5)))
    repo.save(
        _certification(
            "cert-b", name="cert b", worker_id="worker-2", expires_at=NOW + timedelta(days=7)
        )
    )

    inside = repo.list_expiring_between(NOW, NOW + timedelta(days=7))
    assert [item.certification_id for item in inside] == ["cert-a"]
