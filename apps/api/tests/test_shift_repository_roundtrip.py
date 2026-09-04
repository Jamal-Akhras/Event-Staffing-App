from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository

CREATED = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)


def _shift(shift_id: str, **overrides) -> Shift:
    values = dict(
        shift_id=shift_id,
        operator_id="operator-1",
        account_id=None,
        role="Bartender",
        location="Main bar",
        start_time=START,
        end_time=START + timedelta(hours=5),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="open",
        created_at=CREATED,
        updated_at=CREATED,
        workers_needed=1,
        workers_filled=0,
    )
    values.update(overrides)
    return Shift(**values)


def test_every_shift_field_survives_a_sql_round_trip(repo_session):
    repo = SqlAlchemyShiftRepository(repo_session)
    saved = _shift(
        "shift-rt-1",
        origin="assigned",
        assigned_worker_id="worker-1",
        billable=False,
        offer_team_at=START,
        required_certification="Personal Licence",
        rota_state="draft",
        needs_attention=False,
    )
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    loaded = repo.get("shift-rt-1")
    assert loaded == saved


def test_a_parked_shift_survives_a_sql_round_trip(repo_session):
    repo = SqlAlchemyShiftRepository(repo_session)
    saved = _shift(
        "shift-rt-2",
        origin="pool",
        billable=True,
        rota_state="published",
        needs_attention=True,
    )
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    loaded = repo.get("shift-rt-2")
    assert loaded == saved
    assert loaded.needs_attention is True
