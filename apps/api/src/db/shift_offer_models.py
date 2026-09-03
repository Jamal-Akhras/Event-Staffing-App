from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, text

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class ShiftOfferModel(Base):
    __tablename__ = "shift_offers"
    __table_args__ = (
        CheckConstraint("source IN ('rota', 'cover', 'manual')", name="ck_shift_offers_source"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="ck_shift_offers_status",
        ),
        CheckConstraint(
            "response_source IS NULL OR response_source IN ('manual', 'auto')",
            name="ck_shift_offers_response_source",
        ),
        CheckConstraint(
            "(status IN ('accepted', 'declined', 'withdrawn')) = (responded_at IS NOT NULL)",
            name="ck_shift_offers_answer_time",
        ),
        CheckConstraint(
            "(response_source IS NOT NULL) = (status = 'accepted')",
            name="ck_shift_offers_accept_source",
        ),
        Index("ix_shift_offers_worker", "worker_id", "offered_at"),
        Index("ix_shift_offers_shift", "shift_id"),
        Index(
            "uq_shift_offers_one_pending",
            "shift_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )

    offer_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    worker_id = Column(String, nullable=False)
    source = Column(String(12), nullable=False)
    status = Column(String(12), nullable=False)
    offered_at = Column(UtcDateTime(), nullable=False)
    expires_at = Column(UtcDateTime(), nullable=True)
    responded_at = Column(UtcDateTime(), nullable=True)
    response_source = Column(String(12), nullable=True)
