from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.src.deps import get_account_repo
from apps.api.src.main import app
from apps.api.src.models.account import Account

OPERATOR_HEADERS = {
    "X-Actor-Role": "operator",
    "X-Actor-Id": "operator-1",
    "X-Account-Id": "account-1",
}


class FakeAccountRepository:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}

    def get(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    def save(self, account: Account) -> Account:
        self.accounts[account.account_id] = account
        return account


@pytest.fixture
def account_repo() -> FakeAccountRepository:
    repo = FakeAccountRepository()
    repo.save(
        Account(
            account_id="account-1",
            name="Pearl Bar",
            country="GB",
            currency="GBP",
            created_at=datetime(2030, 1, 1, 9, 0, 0),
            venue_type="Restaurant & Bar",
            contact_email="ops@example.com",
            contact_phone="+44 7700 900000",
            default_location="12 King St, London",
            photos=["/uploads/one.jpg"],
        )
    )
    return repo


@pytest.fixture(autouse=True)
def override_account_repo(account_repo: FakeAccountRepository):
    app.dependency_overrides[get_account_repo] = lambda: account_repo
    yield
    app.dependency_overrides.clear()


def test_get_account_returns_default_notification_preferences():
    client = TestClient(app)

    response = client.get("/accounts/me", headers=OPERATOR_HEADERS)

    assert response.status_code == 200
    assert response.json()["notification_preferences"] == {
        "new_applications": True,
        "shift_reminders": True,
        "no_show_alerts": True,
    }


def test_update_account_persists_notification_preferences():
    client = TestClient(app)

    response = client.put(
        "/accounts/me",
        headers=OPERATOR_HEADERS,
        json={
            "notification_preferences": {
                "new_applications": False,
                "shift_reminders": True,
                "no_show_alerts": False,
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["notification_preferences"] == {
        "new_applications": False,
        "shift_reminders": True,
        "no_show_alerts": False,
    }

    reloaded = client.get("/accounts/me", headers=OPERATOR_HEADERS)
    assert reloaded.json()["notification_preferences"]["new_applications"] is False


def test_update_account_drops_unknown_notification_keys():
    client = TestClient(app)

    response = client.put(
        "/accounts/me",
        headers=OPERATOR_HEADERS,
        json={
            "notification_preferences": {
                "new_applications": False,
                "evil_unknown_key": True,
            }
        },
    )

    assert response.status_code == 200
    prefs = response.json()["notification_preferences"]
    assert prefs == {
        "new_applications": False,
        "shift_reminders": True,
        "no_show_alerts": True,
    }
    assert "evil_unknown_key" not in prefs


def test_update_account_rejects_non_bool_notification_values():
    client = TestClient(app)

    response = client.put(
        "/accounts/me",
        headers=OPERATOR_HEADERS,
        json={
            "notification_preferences": {
                "shift_reminders": "not-a-bool",
            }
        },
    )

    assert response.status_code == 422


def test_account_profile_update_still_preserves_existing_fields():
    client = TestClient(app)

    response = client.put(
        "/accounts/me",
        headers=OPERATOR_HEADERS,
        json={
            "name": "Pearl Ballroom",
            "photos": ["/uploads/one.jpg", "/uploads/two.jpg"],
        },
    )

    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Pearl Ballroom"
    assert data["contact_email"] == "ops@example.com"
    assert data["photos"] == ["/uploads/one.jpg", "/uploads/two.jpg"]
    assert data["notification_preferences"]["no_show_alerts"] is True
