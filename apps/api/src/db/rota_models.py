from __future__ import annotations

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class RotaPublicationModel(Base):
    __tablename__ = "rota_publications"
    __table_args__ = (
        UniqueConstraint("venue_id", "week_start", "revision", name="uq_rota_publications_venue_week_revision"),
        CheckConstraint("revision >= 1", name="ck_rota_publications_revision"),
        Index("ix_rota_publications_venue_week", "venue_id", "week_start"),
    )

    publication_id = Column(String, primary_key=True)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    week_start = Column(Date, nullable=False)
    revision = Column(Integer, nullable=False)
    published_at = Column(UtcDateTime(), nullable=False)
    published_by_user_id = Column(String, nullable=False)
    assignments = Column(JSON, nullable=False)
