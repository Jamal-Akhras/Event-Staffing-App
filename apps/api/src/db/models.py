from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    Float,
    ForeignKey,
    func,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import synonym

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime
from packages.domain.src.booking_state import BookingState
from apps.api.src.db.tenancy_models import (
    MarketModel,
    OrganisationMembershipModel,
    OrganisationModel,
    VenueModel,
)
from apps.api.src.db.notification_models import NotificationModel
from apps.api.src.db.trust_models import ReportModel
from apps.api.src.db.idempotency_models import IdempotencyRecordModel

AccountModel = VenueModel


class BookingModel(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("worker_id", "shift_id", name="uq_bookings_worker_shift"),
        CheckConstraint("end_time > start_time", name="ck_bookings_time_order"),
    )

    booking_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="RESTRICT"), nullable=False, index=True)
    worker_id = Column(String, nullable=False, index=True)
    operator_id = Column(String, nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    state = Column(Enum(BookingState), nullable=False, default=BookingState.REQUESTED)

    created_at = Column(UtcDateTime(), nullable=True)
    confirmed_at = Column(UtcDateTime(), nullable=True)
    checked_in_at = Column(UtcDateTime(), nullable=True)
    checked_out_at = Column(UtcDateTime(), nullable=True)
    approved_at = Column(UtcDateTime(), nullable=True)
    paid_at = Column(UtcDateTime(), nullable=True)
    cancelled_at = Column(UtcDateTime(), nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_by_user_id = Column(String, nullable=True)
    no_show_at = Column(UtcDateTime(), nullable=True)
    payment_method = Column(String(30), nullable=True)
    payment_reference = Column(String(200), nullable=True)
    payment_recorded_by_user_id = Column(String, nullable=True)


class ShiftModel(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_shifts_time_order"),
        CheckConstraint("pay_rate >= 0", name="ck_shifts_pay_rate_nonnegative"),
        CheckConstraint("workers_needed >= 1", name="ck_shifts_workers_needed_positive"),
        CheckConstraint("workers_filled >= 0", name="ck_shifts_workers_filled_nonnegative"),
        CheckConstraint("workers_filled <= workers_needed", name="ck_shifts_capacity_bounds"),
        CheckConstraint(
            "status IN ('open', 'filled', 'closed', 'cancelled')",
            name="ck_shifts_status",
        ),
    )

    shift_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=True, index=True)
    account_id = synonym("venue_id")
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    pay_rate = Column(Numeric(12, 2), nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False, server_default=func.now())
    closed_at = Column(UtcDateTime(), nullable=True)
    cancelled_at = Column(UtcDateTime(), nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_by_user_id = Column(String, nullable=True)
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
        CheckConstraint(
            "status IN ('applied', 'approved', 'rejected', 'withdrawn')",
            name="ck_applications_status",
        ),
    )

    application_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="RESTRICT"), nullable=False, index=True)
    worker_id = Column(String, nullable=False, index=True)
    operator_id = Column(String, nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    message = Column(String, nullable=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    decided_at = Column(UtcDateTime(), nullable=True)
    withdrawn_at = Column(UtcDateTime(), nullable=True)
    withdrawal_reason = Column(String(500), nullable=True)


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
    pay_rate = Column(Numeric(12, 2), nullable=True)
    notes = Column(String, nullable=True)
    updated_at = Column(UtcDateTime(), nullable=False)
    avatar_url = Column(String, nullable=True)
    allow_venue_recontact = Column(Boolean, nullable=False, default=False)
    market_id = Column(String, ForeignKey("markets.market_id", ondelete="RESTRICT"), nullable=True, index=True)


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    active_venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = synonym("active_venue_id")
    worker_profile_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
    password_changed_at = Column(UtcDateTime(), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verification_token = Column(String, nullable=True, index=True)
    session_version = Column(Integer, nullable=False, default=0)
    deactivated_at = Column(UtcDateTime(), nullable=True)
    anonymized_at = Column(UtcDateTime(), nullable=True)


class ShiftTemplateModel(Base):
    __tablename__ = "shift_templates"
    __table_args__ = (
        CheckConstraint("duration_hours > 0", name="ck_shift_templates_duration_positive"),
        CheckConstraint("pay_rate >= 0", name="ck_shift_templates_pay_rate_nonnegative"),
        CheckConstraint("workers_needed >= 1", name="ck_shift_templates_workers_needed_positive"),
    )

    template_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=True, index=True)
    account_id = synonym("venue_id")
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=False)
    duration_hours = Column(Float, nullable=False)
    pay_rate = Column(Numeric(12, 2), nullable=False)
    workers_needed = Column(Integer, nullable=False, default=1)
    notes = Column(String, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)


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
    start_date = Column(UtcDateTime(), nullable=False)
    end_date = Column(UtcDateTime(), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(UtcDateTime(), nullable=False)
    last_generated_at = Column(UtcDateTime(), nullable=True)


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


class RatingModel(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("booking_id", "rated_by_role", name="uq_ratings_booking_role"),
        CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )

    rating_id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    rated_by_role = Column(String, nullable=False)
    rater_id = Column(String, nullable=False)
    stars = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)


class WorkerFeedStateModel(Base):
    __tablename__ = "worker_feed_states"
    __table_args__ = (
        CheckConstraint("action IN ('passed')", name="ck_worker_feed_states_action"),
    )

    worker_id = Column(String, primary_key=True)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="CASCADE"), primary_key=True, index=True)
    action = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
