from __future__ import annotations

from typing import Protocol

from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal


class FeedRankingAppealRepository(Protocol):
    def save(self, appeal: FeedRankingAppeal) -> FeedRankingAppeal:
        ...

    def get(self, appeal_id: str) -> FeedRankingAppeal | None:
        ...

    def list_open(self, limit: int) -> list[FeedRankingAppeal]:
        ...

    def list_for_worker(self, worker_id: str) -> list[FeedRankingAppeal]:
        ...
