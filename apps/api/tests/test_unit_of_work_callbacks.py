from __future__ import annotations

import pytest

from apps.api.src.unit_of_work import RequestUnitOfWork


class FakeSession:
    def __init__(self, fail_commit: bool = False) -> None:
        self.fail_commit = fail_commit
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        if self.fail_commit:
            raise RuntimeError("commit failed")

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def test_commit_runs_commit_callbacks_and_discards_rollback_callbacks() -> None:
    events: list[str] = []
    unit_of_work = RequestUnitOfWork(FakeSession())
    unit_of_work.after_commit(lambda: events.append("committed"))
    unit_of_work.after_rollback(lambda: events.append("rolled back"))

    unit_of_work.commit()
    unit_of_work.rollback()

    assert events == ["committed"]


def test_failed_commit_preserves_cleanup_for_rollback() -> None:
    events: list[str] = []
    session = FakeSession(fail_commit=True)
    unit_of_work = RequestUnitOfWork(session)
    unit_of_work.after_rollback(lambda: events.append("cleaned"))

    with pytest.raises(RuntimeError, match="commit failed"):
        unit_of_work.commit()
    unit_of_work.rollback()

    assert session.rolled_back is True
    assert events == ["cleaned"]
