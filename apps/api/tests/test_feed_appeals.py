from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.repository_dependencies import shared_feed_ranking_appeal_repository

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}
STAFF = {"X-Actor-Role": "system", "X-Actor-Id": "staff-1"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_feed_ranking_appeal_repository().clear()
    yield
    shared_feed_ranking_appeal_repository().clear()


def test_a_worker_files_an_appeal_and_staff_reviews_it():
    client = TestClient(main.app)

    filed = client.post(
        "/me/feed-appeals",
        json={"shift_id": "shift-9", "slate_id": "slate-1", "reason": "This ranked far too low for me."},
        headers=WORKER,
    )
    assert filed.status_code == 201, filed.text
    appeal_id = filed.json()["appeal_id"]
    assert filed.json()["reviewed_at"] is None

    mine = client.get("/me/feed-appeals", headers=WORKER).json()
    assert [a["appeal_id"] for a in mine] == [appeal_id]
    assert client.get("/me/feed-appeals", headers=OTHER_WORKER).json() == []

    assert client.get("/system/feed-appeals", headers=WORKER).status_code == 403
    open_appeals = client.get("/system/feed-appeals", headers=STAFF).json()
    assert [a["appeal_id"] for a in open_appeals] == [appeal_id]

    reviewed = client.post(
        f"/system/feed-appeals/{appeal_id}/review",
        json={"outcome_note": "Reviewed — ranking behaved as designed; no change."},
        headers=STAFF,
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["reviewed_at"] is not None
    assert reviewed.json()["outcome_note"].startswith("Reviewed")

    assert client.get("/system/feed-appeals", headers=STAFF).json() == []

    again = client.post(
        f"/system/feed-appeals/{appeal_id}/review",
        json={"outcome_note": "Second look."},
        headers=STAFF,
    )
    assert again.status_code == 400
