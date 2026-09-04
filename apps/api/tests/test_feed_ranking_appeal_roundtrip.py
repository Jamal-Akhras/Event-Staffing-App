from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal
from apps.api.src.repositories.sqlalchemy_feed_ranking_appeal_repository import (
    SqlAlchemyFeedRankingAppealRepository,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)


def _appeal(appeal_id: str, **overrides) -> FeedRankingAppeal:
    values = dict(
        appeal_id=appeal_id,
        worker_id="worker-1",
        shift_id="shift-1",
        slate_id="slate-1",
        reason="Ranked far too low for me.",
        created_at=NOW,
    )
    values.update(overrides)
    return FeedRankingAppeal(**values)


def test_every_appeal_field_survives_a_sql_round_trip(repo_session):
    repo = SqlAlchemyFeedRankingAppealRepository(repo_session)
    saved = _appeal(
        "appeal-rt-1",
        reviewed_at=NOW + timedelta(hours=2),
        reviewed_by_user_id="staff-1",
        outcome_note="Reviewed; no change.",
    )
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    assert repo.get("appeal-rt-1") == saved


def test_open_and_worker_listings(repo_session):
    repo = SqlAlchemyFeedRankingAppealRepository(repo_session)
    repo.save(_appeal("open-1"))
    repo.save(
        _appeal(
            "closed-1",
            reviewed_at=NOW,
            reviewed_by_user_id="staff-1",
            outcome_note="Done.",
        )
    )
    repo.save(_appeal("open-2", worker_id="worker-2"))

    open_ids = {a.appeal_id for a in repo.list_open(50)}
    assert open_ids == {"open-1", "open-2"}
    assert {a.appeal_id for a in repo.list_for_worker("worker-1")} == {"open-1", "closed-1"}
    assert [a.appeal_id for a in repo.list_for_worker("worker-2")] == ["open-2"]
