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
    event,
    false,
    true,
)
from sqlalchemy.orm import synonym

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime
from packages.domain.src.booking_state import BookingState
from packages.domain.src.attendance import new_attendance_code
from apps.api.src.db.tenancy_models import (
    MarketModel,
    OrganisationMembershipModel,
    OrganisationModel,
    VenueModel,
)
from apps.api.src.db.message_models import ApplicationMessageHistoryModel, MessageModel
from apps.api.src.db.notification_models import NotificationModel
from apps.api.src.db.trust_models import ReportModel
from apps.api.src.db.idempotency_models import IdempotencyRecordModel
from apps.api.src.db.billing_models import PartnerCodeModel, PartnerCodeRedemptionModel
from apps.api.src.db.event_models import EventModel
from apps.api.src.db.booking_charge_models import BookingChargeModel
from apps.api.src.db.shift_offer_models import ShiftOfferModel
from apps.api.src.db.certification_models import WorkerCertificationModel
from apps.api.src.db.notification_models import NotificationReceiptModel
from apps.api.src.db.tenancy_models import ManagerInvitationModel
from apps.api.src.db.shift_change_models import ShiftChangeRequestModel, ShiftChangeTransitionModel
from apps.api.src.db.auto_accept_models import AutoAcceptAttemptModel, WorkerAutoAcceptRuleModel
from apps.api.src.db.booking_transition_models import BookingTransitionModel
from apps.api.src.db.workforce_models import (
    RelationshipTransitionModel,
    VenueJoinCodeModel,
    VenueJoinCodeRedemptionModel,
    WorkerRelationshipModel,
)
from apps.api.src.db.template_models import RecurringScheduleModel, ShiftTemplateModel
from apps.api.src.db.rota_models import RotaPublicationModel
from apps.api.src.db.availability_models import (
    AvailabilityExceptionModel,
    AvailabilityRuleModel,
    TimeOffRequestModel,
)

AccountModel = VenueModel


class BookingModel(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("worker_id", "shift_id", name="uq_bookings_worker_shift"),
        CheckConstraint("end_time > start_time", name="ck_bookings_time_order"),
        CheckConstraint("length(check_in_code) = 4", name="ck_bookings_check_in_code_length"),
        CheckConstraint("length(completion_code) = 4", name="ck_bookings_completion_code_length"),
        CheckConstraint("check_in_code <> completion_code", name="ck_bookings_attendance_codes_distinct"),
        CheckConstraint("attendance_mode IN ('pin', 'employed')", name="ck_bookings_attendance_mode"),
        CheckConstraint(
            "(override_checked_in_at IS NULL) = (override_checked_out_at IS NULL)",
            name="ck_bookings_override_pair",
        ),
        CheckConstraint(
            "override_checked_out_at IS NULL OR override_checked_out_at > override_checked_in_at",
            name="ck_bookings_override_order",
        ),
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
    check_in_code = Column(String(4), nullable=False)
    completion_code = Column(String(4), nullable=False)
    attendance_mode = Column(String(12), nullable=False, default="pin", server_default="pin")
    override_checked_in_at = Column(UtcDateTime(), nullable=True)
    override_checked_out_at = Column(UtcDateTime(), nullable=True)


@event.listens_for(BookingModel, "before_insert")
def _set_booking_attendance_codes(_mapper, _connection, target: BookingModel) -> None:
    if not target.check_in_code:
        target.check_in_code = new_attendance_code()
    if not target.completion_code or target.completion_code == target.check_in_code:
        target.completion_code = new_attendance_code(target.check_in_code)


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
        CheckConstraint(
            "origin IN ('assigned', 'team', 'pool', 'market')",
            name="ck_shifts_origin",
        ),
        CheckConstraint(
            "origin <> 'assigned' OR assigned_worker_id IS NOT NULL",
            name="ck_shifts_assigned_has_worker",
        ),
        CheckConstraint("rota_state IN ('draft', 'published')", name="ck_shifts_rota_state"),
        CheckConstraint(
            "rota_state <> 'draft' OR origin = 'assigned'", name="ck_shifts_draft_is_assigned"
        ),
        CheckConstraint(
            "rota_state <> 'draft' OR workers_needed = 1", name="ck_shifts_draft_single_seat"
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
    origin = Column(String(20), nullable=False, default="market", server_default="market")
    assigned_worker_id = Column(String, nullable=True, index=True)
    billable = Column(Boolean, nullable=False, default=True, server_default=true())
    offer_team_at = Column(UtcDateTime(), nullable=True)
    offer_pool_at = Column(UtcDateTime(), nullable=True)
    publish_market_at = Column(UtcDateTime(), nullable=True)
    rota_state = Column(String(12), nullable=False, default="published", server_default="published")
    needs_attention = Column(Boolean, nullable=False, default=False, server_default=false())
    required_certification = Column(String(120), nullable=True)


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
    marketplace_enabled = Column(Boolean, nullable=False, default=True, server_default=true())
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
    sso_provider = Column(String(32), nullable=True)
    sso_subject = Column(String(255), nullable=True)


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
