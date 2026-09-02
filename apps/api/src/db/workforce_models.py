from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime
from apps.api.src.models.worker_relationship import RELATIONSHIP_STATUSES, RELATIONSHIP_TYPES

_TYPE_LIST = ", ".join(f"'{value}'" for value in RELATIONSHIP_TYPES)
_STATUS_LIST = ", ".join(f"'{value}'" for value in RELATIONSHIP_STATUSES)


class WorkerRelationshipModel(Base):
    __tablename__ = "worker_relationships"
    __table_args__ = (
        UniqueConstraint("venue_id", "worker_id", name="uq_worker_relationships_venue_worker"),
        CheckConstraint(f"relationship_type IN ({_TYPE_LIST})", name="ck_worker_relationships_type"),
        CheckConstraint(f"status IN ({_STATUS_LIST})", name="ck_worker_relationships_status"),
        CheckConstraint(
            "contracted_hours_per_week IS NULL OR contracted_hours_per_week >= 0",
            name="ck_worker_relationships_contracted_hours",
        ),
        CheckConstraint("agreed_rate IS NULL OR agreed_rate >= 0", name="ck_worker_relationships_agreed_rate"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_worker_relationships_date_order"),
        Index("ix_worker_relationships_venue_status", "venue_id", "status"),
        Index("ix_worker_relationships_worker", "worker_id"),
    )

    relationship_id = Column(String, primary_key=True)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    worker_id = Column(String, nullable=False)
    relationship_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    default_role = Column(String(80), nullable=True)
    start_date = Column(UtcDateTime(), nullable=True)
    end_date = Column(UtcDateTime(), nullable=True)
    contracted_hours_per_week = Column(Numeric(5, 2), nullable=True)
    agreed_rate = Column(Numeric(12, 2), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
    created_by_user_id = Column(String, nullable=True)


class RelationshipTransitionModel(Base):
    __tablename__ = "relationship_transitions"
    __table_args__ = (
        CheckConstraint(f"to_relationship_type IN ({_TYPE_LIST})", name="ck_relationship_transitions_to_type"),
        CheckConstraint(f"to_status IN ({_STATUS_LIST})", name="ck_relationship_transitions_to_status"),
        Index("ix_relationship_transitions_relationship", "relationship_id", "occurred_at"),
    )

    transition_id = Column(String, primary_key=True)
    relationship_id = Column(
        String,
        ForeignKey("worker_relationships.relationship_id", ondelete="CASCADE"),
        nullable=False,
    )
    from_relationship_type = Column(String(20), nullable=True)
    to_relationship_type = Column(String(20), nullable=False)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    occurred_at = Column(UtcDateTime(), nullable=False)
    actor_user_id = Column(String, nullable=True)
    reason = Column(String(500), nullable=True)


class VenueJoinCodeModel(Base):
    __tablename__ = "venue_join_codes"
    __table_args__ = (
        CheckConstraint(f"default_relationship_type IN ({_TYPE_LIST})", name="ck_venue_join_codes_type"),
        CheckConstraint("max_redemptions >= 1", name="ck_venue_join_codes_max_redemptions"),
        Index("ix_venue_join_codes_venue", "venue_id"),
    )

    code = Column(String(40), primary_key=True)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="CASCADE"), nullable=False)
    default_relationship_type = Column(String(20), nullable=False)
    default_role = Column(String(80), nullable=True)
    max_redemptions = Column(Integer, nullable=False)
    expires_at = Column(UtcDateTime(), nullable=True)
    revoked_at = Column(UtcDateTime(), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    created_by_user_id = Column(String, nullable=False)


class VenueJoinCodeRedemptionModel(Base):
    __tablename__ = "venue_join_code_redemptions"
    __table_args__ = (
        UniqueConstraint("code", "worker_id", name="uq_venue_join_code_redemptions_code_worker"),
        Index("ix_venue_join_code_redemptions_code", "code"),
    )

    redemption_id = Column(String, primary_key=True)
    code = Column(String(40), ForeignKey("venue_join_codes.code", ondelete="CASCADE"), nullable=False)
    venue_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
    relationship_id = Column(
        String,
        ForeignKey("worker_relationships.relationship_id", ondelete="CASCADE"),
        nullable=False,
    )
    redeemed_at = Column(UtcDateTime(), nullable=False)
