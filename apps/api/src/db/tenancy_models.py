from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import synonym

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class MarketModel(Base):
    __tablename__ = "markets"
    __table_args__ = (
        CheckConstraint("high_pay_threshold >= 0", name="ck_markets_high_pay_nonnegative"),
    )

    market_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), nullable=False)
    timezone = Column(String, nullable=False)
    high_pay_threshold = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)


class OrganisationModel(Base):
    __tablename__ = "organisations"

    organisation_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)


class VenueModel(Base):
    __tablename__ = "venues"

    venue_id = Column(String, primary_key=True)
    account_id = synonym("venue_id")
    organisation_id = Column(
        String,
        ForeignKey("organisations.organisation_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    market_id = Column(
        String,
        ForeignKey("markets.market_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    venue_type = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    default_location = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    photos = Column(JSON, nullable=True)
    notification_preferences = Column(JSON, nullable=True)
    escalation_policy = Column(JSON, nullable=True)


class OrganisationMembershipModel(Base):
    __tablename__ = "organisation_memberships"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'admin', 'manager')", name="ck_memberships_role"),
    )

    organisation_id = Column(
        String,
        ForeignKey("organisations.organisation_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        String,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    role = Column(String, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
