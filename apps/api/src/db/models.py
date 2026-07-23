from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)

from apps.api.src.db.database import Base
from packages.domain.src.booking_state import BookingState


class AccountModel(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime, nullable=False)
    venue_type = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    default_location = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    photos = Column(JSON, nullable=True)
    notification_preferences = Column(JSON, nullable=True)


class BookingModel(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("worker_id", "shift_id", name="uq_bookings_worker_shift"),
        CheckConstraint("end_time > start_time", name="ck_bookings_time_order"),
    )

    booking_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, nullable=False, index=True)
    operator_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    state = Column(Enum(BookingState), nullable=False, default=BookingState.REQUESTED)

    created_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    no_show_at = Column(DateTime, nullable=True)


class ShiftModel(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_shifts_time_order"),
        CheckConstraint("pay_rate >= 0", name="ck_shifts_pay_rate_nonnegative"),
        CheckConstraint("workers_needed >= 1", name="ck_shifts_workers_needed_positive"),
        CheckConstraint("workers_filled >= 0", name="ck_shifts_workers_filled_nonnegative"),
        CheckConstraint("workers_filled <= workers_needed", name="ck_shifts_capacity_bounds"),
    )

    shift_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True)
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    pay_rate = Column(Float, nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    workers_needed = Column(Integer, nullable=False, default=1)
    workers_filled = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class ApplicationModel(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("worker_id", "shift_id", name="uq_applications_worker_shift"),
        CheckConstraint("end_time > start_time", name="ck_applications_time_order"),
        CheckConstraint("status IN ('applied', 'approved', 'rejected')", name="ck_applications_status"),
    )

    application_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String, nullable=False, index=True)
    operator_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    decided_at = Column(DateTime, nullable=True)


class WorkerProfileModel(Base):
    __tablename__ = "worker_profiles"
    __table_args__ = (
        CheckConstraint("experience_years >= 0", name="ck_worker_profiles_experience_nonnegative"),
        CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 1",
            name="ck_worker_profiles_reliability_range",
        ),
        CheckConstraint("pay_rate IS NULL OR pay_rate >= 0", name="ck_worker_profiles_pay_rate_nonnegative"),
    )

    worker_id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    city = Column(String, nullable=False)
    experience_years = Column(Integer, nullable=False)
    reliability_score = Column(Float, nullable=False)
    badges = Column(JSON, nullable=False)
    bio = Column(String, nullable=True)
    languages = Column(JSON, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    emergency_contact = Column(String, nullable=True)
    pay_rate = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=False)
    avatar_url = Column(String, nullable=True)
    allow_venue_recontact = Column(Boolean, nullable=False, default=False)


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True)
    worker_profile_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    password_changed_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verification_token = Column(String, nullable=True, index=True)


class ShiftTemplateModel(Base):
    __tablename__ = "shift_templates"
    __table_args__ = (
        CheckConstraint("duration_hours > 0", name="ck_shift_templates_duration_positive"),
        CheckConstraint("pay_rate >= 0", name="ck_shift_templates_pay_rate_nonnegative"),
        CheckConstraint("workers_needed >= 1", name="ck_shift_templates_workers_needed_positive"),
    )

    template_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    account_id = Column(String, ForeignKey("accounts.account_id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    duration_hours = Column(Float, nullable=False)
    pay_rate = Column(Float, nullable=False)
    workers_needed = Column(Integer, nullable=False, default=1)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class RecurringScheduleModel(Base):
    __tablename__ = "recurring_schedules"
    __table_args__ = (
        CheckConstraint("frequency IN ('daily', 'weekly', 'monthly')", name="ck_recurring_schedules_frequency"),
        CheckConstraint(
            "day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)",
            name="ck_recurring_schedules_day_of_week",
        ),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_recurring_schedules_date_order"),
    )

    schedule_id = Column(String, primary_key=True)
    template_id = Column(
        String,
        ForeignKey("shift_templates.template_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operator_id = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=True)
    time_of_day = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    last_generated_at = Column(DateTime, nullable=True)


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
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


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
    edited_at = Column(DateTime, nullable=False)


class NotificationModel(Base):
    __tablename__ = "notifications"

    notification_id = Column(String, primary_key=True)
    worker_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="SET NULL"), nullable=True)
    read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)


class RatingModel(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("booking_id", "rated_by_role", name="uq_ratings_booking_role"),
        CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )

    rating_id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    rated_by_role = Column(String, nullable=False)
    stars = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


class WorkerFeedStateModel(Base):
    __tablename__ = "worker_feed_states"
    __table_args__ = (
        CheckConstraint("action IN ('passed')", name="ck_worker_feed_states_action"),
    )

    worker_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), primary_key=True, index=True)
    action = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
