from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, JSON, String

from apps.api.src.db.database import Base
from packages.domain.src.booking_state import BookingState


class BookingModel(Base):
    __tablename__ = "bookings"

    booking_id = Column(String, primary_key=True)
    shift_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
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

    shift_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
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


class ApplicationModel(Base):
    __tablename__ = "applications"

    application_id = Column(String, primary_key=True)
    shift_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=True)
    booking_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    decided_at = Column(DateTime, nullable=True)


class WorkerProfileModel(Base):
    __tablename__ = "worker_profiles"

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


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    worker_profile_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
