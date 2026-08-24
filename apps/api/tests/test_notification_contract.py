from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context
from apps.api.src.deps import get_notification_repo, get_request_session
from apps.api.src.main import app
from apps.api.src.models.notification import Notification
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository


def test_worker_inbox_cursor_read_and_tenant_isolation():
    repo = InMemoryNotificationRepository()
    now = datetime(2030, 1, 1, tzinfo=UTC)
    for index in range(3):
        repo.save(
            Notification(
                notification_id=f"notification-{index}",
                worker_id="worker-1",
                type="application.approved",
                title="Application approved",
                body="You are booked.",
                created_at=now + timedelta(minutes=index),
                action_kind="application",
                action_entity_id=f"application-{index}",
            )
        )
    repo.save(
        Notification(
            notification_id="someone-else",
            worker_id="worker-2",
            type="application.rejected",
            title="Not selected",
            body="Another worker's notification.",
            created_at=now,
        )
    )
    app.dependency_overrides[get_notification_repo] = lambda: repo
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        user_id="user-1",
        role=ActorRole.WORKER,
        worker_profile_id="worker-1",
    )
    client = TestClient(app)

    first = client.get("/notifications?limit=2")
    assert first.status_code == 200
    assert [item["notification_id"] for item in first.json()["items"]] == [
        "notification-2",
        "notification-1",
    ]
    assert first.json()["unread_count"] == 3
    assert first.json()["items"][0]["action"] == {
        "kind": "application",
        "entity_id": "application-2",
    }

    second = client.get("/notifications", params={"limit": 2, "cursor": first.json()["next_cursor"]})
    assert [item["notification_id"] for item in second.json()["items"]] == ["notification-0"]

    marked = client.post("/notifications/notification-2/read")
    assert marked.status_code == 200
    assert client.get("/notifications").json()["unread_count"] == 2
    assert client.post("/notifications/someone-else/read").status_code == 404
    assert client.post("/notifications/read-all").json() == {"marked_read": 2}


def test_preferences_and_push_token_are_actor_scoped():
    app.dependency_overrides[get_request_session] = lambda: None
    app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        user_id="settings-user",
        role=ActorRole.WORKER,
        worker_profile_id="settings-worker",
    )
    client = TestClient(app)
    defaults = client.get("/notification-preferences")
    assert defaults.status_code == 200
    payload = defaults.json()
    payload["channels"]["push"] = False

    updated = client.put("/notification-preferences", json=payload)
    assert updated.status_code == 200
    assert updated.json()["channels"]["push"] is False

    created = client.post(
        "/devices/push-tokens",
        json={"token": "ExponentPushToken[test]", "platform": "ios", "device_id": "device-1"},
    )
    assert created.status_code == 200
    push_token_id = created.json()["push_token_id"]
    assert client.delete(f"/devices/push-tokens/{push_token_id}").status_code == 200
    assert client.delete(f"/devices/push-tokens/{push_token_id}").status_code == 404
