from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.src import main
from apps.api.src.db.models import OrganisationModel, UserModel, VenueModel
from apps.api.src.db.notification_models import OutboxEventModel
from apps.api.src.repositories.sqlalchemy_market_repository import SqlAlchemyMarketRepository
from apps.api.src.repositories.sqlalchemy_organisation_repository import SqlAlchemyOrganisationRepository
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository

pytestmark = pytest.mark.postgres

INVITE_CODE = "transaction-test-invite"
PASSWORD = "transaction-pass-1"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    return TestClient(main.app, raise_server_exceptions=False)


def _operator_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": PASSWORD,
        "venue_name": "Atomic Tavern",
        "country": "GB",
        "market_id": "bath-gb",
        "invite_code": INVITE_CODE,
    }


def test_registration_repositories_share_one_request_session(client, monkeypatch):
    sessions: list[object] = []
    market_init = SqlAlchemyMarketRepository.__init__
    organisation_init = SqlAlchemyOrganisationRepository.__init__
    user_init = SqlAlchemyUserRepository.__init__

    def capture_market(self, session):
        sessions.append(session)
        market_init(self, session)

    def capture_organisation(self, session):
        sessions.append(session)
        organisation_init(self, session)

    def capture_user(self, session):
        sessions.append(session)
        user_init(self, session)

    monkeypatch.setattr(SqlAlchemyMarketRepository, "__init__", capture_market)
    monkeypatch.setattr(SqlAlchemyOrganisationRepository, "__init__", capture_organisation)
    monkeypatch.setattr(SqlAlchemyUserRepository, "__init__", capture_user)

    response = client.post(
        "/auth/register/operator",
        json=_operator_payload("shared-session@example.com"),
    )

    assert response.status_code == 200, response.text
    assert len(sessions) == 3
    assert len({id(session) for session in sessions}) == 1


def test_registration_rolls_back_every_repository_write(client, monkeypatch):
    def fail_user_save(_self, _user):
        raise RuntimeError("forced failure after account write")

    monkeypatch.setattr(SqlAlchemyUserRepository, "save", fail_user_save)
    response = client.post(
        "/auth/register/operator",
        json=_operator_payload("rollback@example.com"),
    )

    assert response.status_code == 500

    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session:
        organisation_count = session.scalar(select(func.count()).select_from(OrganisationModel))
        venue_count = session.scalar(select(func.count()).select_from(VenueModel))
        user_count = session.scalar(select(func.count()).select_from(UserModel))
    assert organisation_count == 0
    assert venue_count == 0
    assert user_count == 0


def test_verification_email_is_committed_atomically_with_user(client):
    response = client.post(
        "/auth/register/operator",
        json=_operator_payload("after-commit@example.com"),
    )

    assert response.status_code == 200, response.text
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session:
        user_count = session.scalar(
            select(func.count()).select_from(UserModel).where(
                UserModel.email == "after-commit@example.com"
            )
        )
        event = session.scalar(
            select(OutboxEventModel).where(OutboxEventModel.event_type == "auth.verify_email")
        )
    assert user_count == 1
    assert event.payload["recipients"][0]["id"] == "after-commit@example.com"
