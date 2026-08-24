from __future__ import annotations

from typing import Protocol

from apps.api.src.models.worker_feed_query import WorkerFeedItem, WorkerFeedQuery


class WorkerFeedQueryRepository(Protocol):
    def list_page(self, query: WorkerFeedQuery) -> list[WorkerFeedItem]:
        raise NotImplementedError
