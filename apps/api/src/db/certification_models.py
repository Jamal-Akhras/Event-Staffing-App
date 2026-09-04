from __future__ import annotations

from sqlalchemy import Column, Index, String, UniqueConstraint

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class WorkerCertificationModel(Base):
    __tablename__ = "worker_certifications"
    __table_args__ = (
        UniqueConstraint("worker_id", "name", name="uq_worker_certifications_worker_name"),
        Index("ix_worker_certifications_expiry", "worker_id", "expires_at"),
    )

    certification_id = Column(String, primary_key=True)
    worker_id = Column(String, nullable=False)
    name = Column(String(120), nullable=False)
    display_name = Column(String(120), nullable=False)
    expires_at = Column(UtcDateTime(), nullable=False)
    reference = Column(String(120), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
