from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

RELATIONSHIP_TYPES = ("permanent", "part_time", "bank", "pool", "one_off")
RELATIONSHIP_STATUSES = ("invited", "active", "ended")

EMPLOYED_TYPES = ("permanent", "part_time", "bank")


@dataclass(frozen=True)
class WorkerRelationship:
    relationship_id: str
    venue_id: str
    worker_id: str
    relationship_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    default_role: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    contracted_hours_per_week: Decimal | None = None
    agreed_rate: Decimal | None = None
    created_by_user_id: str | None = None


@dataclass(frozen=True)
class RelationshipTransition:
    transition_id: str
    relationship_id: str
    to_relationship_type: str
    to_status: str
    occurred_at: datetime
    from_relationship_type: str | None = None
    from_status: str | None = None
    actor_user_id: str | None = None
    reason: str | None = None
