from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_template_repo
from apps.api.src.repositories.in_memory_template_repository import (
    InMemoryTemplateRepository,
)

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}


def _client() -> TestClient:
    template_repo = InMemoryTemplateRepository()
    main.app.dependency_overrides.clear()
    main.app.dependency_overrides[get_template_repo] = lambda: template_repo
    return TestClient(main.app)


def test_template_create_list_update_delete_round_trip():
    client = _client()

    create = client.post(
        "/templates",
        json={
            "name": "Friday Bar",
            "role": "Bartender",
            "location": "Main Room",
            "duration_hours": 6,
            "pay_rate": 32,
            "workers_needed": 2,
            "notes": "Black attire",
        },
        headers=OPERATOR_HEADERS,
    )
    assert create.status_code == 200
    template_id = create.json()["template_id"]
    assert create.json()["operator_id"] == "operator-1"

    listed = client.get("/templates", headers=OPERATOR_HEADERS)
    assert listed.status_code == 200
    assert listed.json()[0]["template_id"] == template_id

    updated = client.put(
        f"/templates/{template_id}",
        json={
            "name": "Friday Bar Team",
            "role": "Bartender",
            "location": "Main Room",
            "duration_hours": 6,
            "pay_rate": 34,
            "workers_needed": 3,
            "notes": "Black attire",
        },
        headers=OPERATOR_HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["workers_needed"] == 3

    deleted = client.delete(
        f"/templates/{template_id}",
        headers=OPERATOR_HEADERS,
    )
    assert deleted.status_code == 200

    empty = client.get("/templates", headers=OPERATOR_HEADERS)
    assert empty.status_code == 200
    assert empty.json() == []


def test_default_template_dependency_uses_in_memory(monkeypatch):
    monkeypatch.setenv("USE_IN_MEMORY", "true")
    repo_generator = get_template_repo()
    repo = next(repo_generator)
    try:
        assert isinstance(repo, InMemoryTemplateRepository)
    finally:
        repo_generator.close()
