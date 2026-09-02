from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.worker_relationship import RelationshipTransition, WorkerRelationship
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)


def save_relationship(
    repo: WorkerRelationshipRepository,
    existing: WorkerRelationship | None,
    venue_id: str,
    worker_id: str,
    relationship_type: str,
    now: datetime,
    actor_user_id: str | None,
    default_role: str | None,
    status: str = "active",
    end_date: datetime | None = None,
) -> WorkerRelationship:
    if existing is None:
        return repo.save(
            WorkerRelationship(
                relationship_id=str(uuid4()),
                venue_id=venue_id,
                worker_id=worker_id,
                relationship_type=relationship_type,
                status=status,
                created_at=now,
                updated_at=now,
                default_role=default_role,
                start_date=now,
                end_date=end_date,
                created_by_user_id=actor_user_id,
            )
        )
    return repo.save(
        replace(
            existing,
            relationship_type=relationship_type,
            status=status,
            updated_at=now,
            end_date=end_date,
            default_role=default_role or existing.default_role,
        )
    )


def record_transition(
    repo: RelationshipTransitionRepository,
    previous: WorkerRelationship | None,
    current: WorkerRelationship,
    now: datetime,
    actor_user_id: str | None,
    reason: str | None,
) -> None:
    repo.record(
        RelationshipTransition(
            transition_id=str(uuid4()),
            relationship_id=current.relationship_id,
            to_relationship_type=current.relationship_type,
            to_status=current.status,
            occurred_at=now,
            from_relationship_type=previous.relationship_type if previous else None,
            from_status=previous.status if previous else None,
            actor_user_id=actor_user_id,
            reason=reason,
        )
    )
