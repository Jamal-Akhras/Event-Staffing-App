from __future__ import annotations

from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal


class InMemoryFeedRankingAppealRepository:
    def __init__(self) -> None:
        self._items: dict[str, FeedRankingAppeal] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, appeal: FeedRankingAppeal) -> FeedRankingAppeal:
        self._items[appeal.appeal_id] = appeal
        return appeal

    def get(self, appeal_id: str) -> FeedRankingAppeal | None:
        return self._items.get(appeal_id)

    def list_open(self, limit: int) -> list[FeedRankingAppeal]:
        rows = [item for item in self._items.values() if item.reviewed_at is None]
        return sorted(rows, key=lambda item: item.created_at)[:limit]

    def list_for_worker(self, worker_id: str) -> list[FeedRankingAppeal]:
        rows = [item for item in self._items.values() if item.worker_id == worker_id]
        return sorted(rows, key=lambda item: item.created_at, reverse=True)
