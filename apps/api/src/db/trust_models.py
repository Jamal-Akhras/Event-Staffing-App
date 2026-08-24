from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("reporter_role IN ('worker', 'operator')", name="ck_reports_reporter_role"),
        CheckConstraint(
            "subject_type IN ('venue', 'shift', 'application', 'booking', 'message')",
            name="ck_reports_subject_type",
        ),
        CheckConstraint(
            "category IN ('safety', 'harassment', 'payment', 'no_show', 'fraud', 'other')",
            name="ck_reports_category",
        ),
        CheckConstraint(
            "status IN ('submitted', 'reviewing', 'resolved', 'dismissed')",
            name="ck_reports_status",
        ),
        Index("ix_reports_reporter_created", "reporter_user_id", "created_at"),
        Index("ix_reports_subject", "subject_type", "subject_id"),
        Index("ix_reports_status_created", "status", "created_at"),
    )

    report_id = Column(String, primary_key=True)
    reporter_user_id = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    reporter_role = Column(String(20), nullable=False)
    subject_type = Column(String(30), nullable=False)
    subject_id = Column(String, nullable=False)
    category = Column(String(30), nullable=False)
    description = Column(String(2000), nullable=False)
    status = Column(String(20), nullable=False, default="submitted")
    resolution_notes = Column(String(2000), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
