from __future__ import annotations

from sqlalchemy import JSON, Column, ForeignKey, Index, String, UniqueConstraint

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class IdempotencyRecordModel(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("user_id", "scope", "key", name="uq_idempotency_actor_scope_key"),
        Index("ix_idempotency_expires_at", "expires_at"),
    )

    record_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    scope = Column(String(100), nullable=False)
    key = Column(String(100), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_payload = Column(JSON, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    expires_at = Column(UtcDateTime(), nullable=False)
