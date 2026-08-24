from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, JSON, String, UniqueConstraint

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class NotificationModel(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_worker_unread_created", "worker_id", "read", "created_at"),
        Index("ix_notifications_venue_unread_created", "venue_id", "read", "created_at"),
    )

    notification_id = Column(String, primary_key=True)
    worker_id = Column(String, nullable=True, index=True)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="SET NULL"), nullable=True)
    action_kind = Column(String(32), nullable=True)
    action_entity_id = Column(String, nullable=True)
    delivery_id = Column(String, unique=True, nullable=True)
    read = Column(Boolean, nullable=False, default=False)
    created_at = Column(UtcDateTime(), nullable=False)


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_events_pending", "available_at", "occurred_at"),
    )

    event_id = Column(String, primary_key=True)
    event_type = Column(String(100), nullable=False)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    occurred_at = Column(UtcDateTime(), nullable=False)
    available_at = Column(UtcDateTime(), nullable=False, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    locked_at = Column(UtcDateTime(), nullable=True)
    locked_by = Column(String(100), nullable=True)
    processed_at = Column(UtcDateTime(), nullable=True)
    last_error = Column(String(1000), nullable=True)
    dead_lettered_at = Column(UtcDateTime(), nullable=True)


class NotificationDeliveryModel(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        CheckConstraint("recipient_kind IN ('worker', 'venue', 'email')", name="ck_notification_deliveries_recipient_kind"),
        CheckConstraint("channel IN ('in_app', 'email', 'push')", name="ck_notification_deliveries_channel"),
        CheckConstraint("status IN ('pending', 'delivered', 'dead_letter')", name="ck_notification_deliveries_status"),
        Index("ix_notification_deliveries_pending", "status", "next_attempt_at"),
    )

    delivery_id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("outbox_events.event_id", ondelete="CASCADE"), nullable=False)
    recipient_kind = Column(String(20), nullable=False)
    recipient_id = Column(String, nullable=False)
    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(UtcDateTime(), nullable=False, index=True)
    locked_at = Column(UtcDateTime(), nullable=True)
    locked_by = Column(String(100), nullable=True)
    delivered_at = Column(UtcDateTime(), nullable=True)
    last_error = Column(String(1000), nullable=True)
    idempotency_key = Column(String(255), nullable=False, unique=True)


class UserNotificationPreferenceModel(Base):
    __tablename__ = "user_notification_preferences"

    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    channels = Column(JSON, nullable=False)
    categories = Column(JSON, nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)


class PushTokenModel(Base):
    __tablename__ = "push_tokens"
    __table_args__ = (
        CheckConstraint("platform IN ('ios', 'android')", name="ck_push_tokens_platform"),
        UniqueConstraint("user_id", "device_id", name="uq_push_tokens_user_device"),
    )

    push_token_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), nullable=False, unique=True)
    platform = Column(String(10), nullable=False)
    device_id = Column(String(255), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
    last_seen_at = Column(UtcDateTime(), nullable=False)
    revoked_at = Column(UtcDateTime(), nullable=True)
