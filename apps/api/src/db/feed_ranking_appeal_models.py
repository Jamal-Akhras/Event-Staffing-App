from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, Index, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class FeedRankingAppealModel(Base):
    __tablename__ = "feed_ranking_appeals"
    __table_args__ = (
        CheckConstraint(
            "(reviewed_at IS NULL) = (reviewed_by_user_id IS NULL)",
            name="ck_feed_ranking_appeals_review",
        ),
        Index("ix_feed_ranking_appeals_open", "reviewed_at", "created_at"),
        Index("ix_feed_ranking_appeals_worker", "worker_id", "created_at"),
    )

    appeal_id = Column(String, primary_key=True)
    worker_id = Column(String, nullable=False)
    shift_id = Column(String, nullable=False)
    slate_id = Column(String, nullable=True)
    reason = Column(String(1000), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    reviewed_at = Column(UtcDateTime(), nullable=True)
    reviewed_by_user_id = Column(String, nullable=True)
    outcome_note = Column(String(1000), nullable=True)
