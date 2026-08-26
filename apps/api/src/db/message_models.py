from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "application_id IS NOT NULL OR booking_id IS NOT NULL",
            name="ck_messages_context_present",
        ),
    )

    message_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(
        String,
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=True, index=True)
    sender_id = Column(String, nullable=False)
    sender_role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    read_at = Column(UtcDateTime(), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)


class ApplicationMessageHistoryModel(Base):
    __tablename__ = "application_message_history"

    history_id = Column(String, primary_key=True)
    application_id = Column(
        String,
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = Column(String, nullable=False)
    edited_at = Column(UtcDateTime(), nullable=False)
