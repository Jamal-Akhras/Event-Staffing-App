from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal
from apps.api.src.repositories.feed_ranking_appeal_repository import (
    FeedRankingAppealRepository,
)
from apps.api.src.services.errors import NotFoundError, ValidationError


class FeedAppealService:
    def __init__(self, appeals: FeedRankingAppealRepository) -> None:
        self._appeals = appeals

    def file(
        self, worker_id: str, shift_id: str, slate_id: str | None, reason: str, now: datetime
    ) -> FeedRankingAppeal:
        return self._appeals.save(
            FeedRankingAppeal(
                appeal_id=str(uuid4()),
                worker_id=worker_id,
                shift_id=shift_id,
                slate_id=slate_id,
                reason=reason,
                created_at=now,
            )
        )

    def list_open(self, limit: int) -> list[FeedRankingAppeal]:
        return self._appeals.list_open(limit)

    def list_for_worker(self, worker_id: str) -> list[FeedRankingAppeal]:
        return self._appeals.list_for_worker(worker_id)

    def review(
        self, appeal_id: str, reviewer_user_id: str, outcome_note: str, now: datetime
    ) -> FeedRankingAppeal:
        appeal = self._appeals.get(appeal_id)
        if appeal is None:
            raise NotFoundError("That appeal was not found.")
        if appeal.reviewed_at is not None:
            raise ValidationError("This appeal has already been reviewed.")
        return self._appeals.save(
            replace(
                appeal,
                reviewed_at=now,
                reviewed_by_user_id=reviewer_user_id,
                outcome_note=outcome_note,
            )
        )
