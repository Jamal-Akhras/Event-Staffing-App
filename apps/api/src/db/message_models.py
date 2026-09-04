from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, UniqueConstraint, text

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class MessageModel(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True)
    thread_id = Column(
        String,
        ForeignKey("message_threads.thread_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sender_id = Column(String, nullable=False)
    sender_role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)


class MessageThreadModel(Base):
    __tablename__ = "message_threads"
    __table_args__ = (
        CheckConstraint(
            "(kind = 'direct' AND shift_id IS NOT NULL AND worker_id IS NOT NULL "
            "AND relationship_id IS NULL AND (application_id IS NOT NULL OR booking_id IS NOT NULL)) "
            "OR (kind = 'shift_group' AND shift_id IS NOT NULL AND worker_id IS NULL "
            "AND application_id IS NULL AND booking_id IS NULL AND relationship_id IS NULL) "
            "OR (kind = 'employment' AND shift_id IS NULL AND worker_id IS NOT NULL "
            "AND application_id IS NULL AND booking_id IS NULL AND relationship_id IS NOT NULL)",
            name="ck_message_threads_shape",
        ),
        Index(
            "uq_message_threads_shift_group",
            "shift_id",
            unique=True,
            sqlite_where=text("kind = 'shift_group'"),
            postgresql_where=text("kind = 'shift_group'"),
        ),
        Index(
            "uq_message_threads_employment",
            "relationship_id",
            unique=True,
            sqlite_where=text("kind = 'employment'"),
            postgresql_where=text("kind = 'employment'"),
        ),
        Index(
            "uq_message_threads_direct_worker",
            "shift_id",
            "worker_id",
            unique=True,
            sqlite_where=text("kind = 'direct'"),
            postgresql_where=text("kind = 'direct'"),
        ),
    )

    thread_id = Column(String, primary_key=True)
    kind = Column(String(16), nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False, index=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="RESTRICT"), nullable=True, index=True)
    application_id = Column(
        String,
        ForeignKey("applications.application_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="RESTRICT"), nullable=True, index=True)
    relationship_id = Column(
        String,
        ForeignKey("worker_relationships.relationship_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    worker_id = Column(String, nullable=True, index=True)
    role_snapshot = Column(String, nullable=True)
    venue_name_snapshot = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)


class MessageThreadParticipantModel(Base):
    __tablename__ = "message_thread_participants"
    __table_args__ = (
        CheckConstraint(
            "(party_kind = 'user' AND user_id IS NOT NULL AND worker_id IS NULL) "
            "OR (party_kind = 'worker' AND worker_id IS NOT NULL AND user_id IS NULL)",
            name="ck_message_thread_participants_party",
        ),
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_message_thread_participants_interval",
        ),
        Index(
            "uq_message_thread_participants_active_user",
            "thread_id",
            "user_id",
            unique=True,
            sqlite_where=text("left_at IS NULL AND party_kind = 'user'"),
            postgresql_where=text("left_at IS NULL AND party_kind = 'user'"),
        ),
        Index(
            "uq_message_thread_participants_active_worker",
            "thread_id",
            "worker_id",
            unique=True,
            sqlite_where=text("left_at IS NULL AND party_kind = 'worker'"),
            postgresql_where=text("left_at IS NULL AND party_kind = 'worker'"),
        ),
    )

    participant_id = Column(String, primary_key=True)
    thread_id = Column(
        String,
        ForeignKey("message_threads.thread_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_kind = Column(String(8), nullable=False)
    user_id = Column(String, nullable=True)
    worker_id = Column(String, nullable=True)
    joined_at = Column(UtcDateTime(), nullable=False)
    left_at = Column(UtcDateTime(), nullable=True)


class MessageReadReceiptModel(Base):
    __tablename__ = "message_read_receipts"
    __table_args__ = (
        CheckConstraint(
            "(party_kind = 'user' AND user_id IS NOT NULL AND worker_id IS NULL) "
            "OR (party_kind = 'worker' AND worker_id IS NOT NULL AND user_id IS NULL)",
            name="ck_message_read_receipts_party",
        ),
        UniqueConstraint("message_id", "user_id", name="uq_message_read_receipts_user"),
        UniqueConstraint("message_id", "worker_id", name="uq_message_read_receipts_worker"),
    )

    receipt_id = Column(String, primary_key=True)
    message_id = Column(
        String,
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_kind = Column(String(8), nullable=False)
    user_id = Column(String, nullable=True)
    worker_id = Column(String, nullable=True)
    read_at = Column(UtcDateTime(), nullable=False)


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
