from __future__ import annotations

from dataclasses import fields

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from apps.api.src.db.feed_ranking_appeal_models import FeedRankingAppealModel
from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal

_FIELDS = tuple(field.name for field in fields(FeedRankingAppeal))


class SqlAlchemyFeedRankingAppealRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, appeal: FeedRankingAppeal) -> FeedRankingAppeal:
        model = self._session.get(FeedRankingAppealModel, appeal.appeal_id)
        if model is None:
            model = FeedRankingAppealModel(appeal_id=appeal.appeal_id)
            self._session.add(model)
        for name in _FIELDS:
            setattr(model, name, getattr(appeal, name))
        self._session.flush()
        return appeal

    def get(self, appeal_id: str) -> FeedRankingAppeal | None:
        model = self._session.get(FeedRankingAppealModel, appeal_id)
        return _to_domain(model) if model is not None else None

    def list_open(self, limit: int) -> list[FeedRankingAppeal]:
        rows = (
            self._session.query(FeedRankingAppealModel)
            .filter(FeedRankingAppealModel.reviewed_at.is_(None))
            .order_by(asc(FeedRankingAppealModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_for_worker(self, worker_id: str) -> list[FeedRankingAppeal]:
        rows = (
            self._session.query(FeedRankingAppealModel)
            .filter(FeedRankingAppealModel.worker_id == worker_id)
            .order_by(desc(FeedRankingAppealModel.created_at))
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: FeedRankingAppealModel) -> FeedRankingAppeal:
    return FeedRankingAppeal(**{name: getattr(model, name) for name in _FIELDS})
