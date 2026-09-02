from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.worker_relationship import (
    EMPLOYED_TYPES,
    RELATIONSHIP_TYPES,
    RelationshipTransition,
    WorkerRelationship,
)
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.relationship_store import record_transition, save_relationship


@dataclass(frozen=True)
class PendingInvitation:
    relationship: WorkerRelationship
    target_type: str


class RelationshipService:
    def __init__(
        self,
        relationships: WorkerRelationshipRepository,
        transitions: RelationshipTransitionRepository,
        workers: WorkerProfileRepository,
    ) -> None:
        self._relationships = relationships
        self._transitions = transitions
        self._workers = workers

    def get(self, venue_id: str, worker_id: str) -> WorkerRelationship | None:
        return self._relationships.get_for_venue_worker(venue_id, worker_id)

    def list_for_venue(self, venue_id: str) -> list[WorkerRelationship]:
        return self._relationships.list_for_venue(venue_id)

    def establish(
        self,
        venue_id: str,
        worker_id: str,
        relationship_type: str,
        now: datetime,
        actor_user_id: str | None = None,
        reason: str | None = None,
        default_role: str | None = None,
    ) -> WorkerRelationship:
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValidationError(f"Unknown relationship type '{relationship_type}'.")

        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is not None and existing.relationship_type == relationship_type and existing.status == "active":
            return existing

        relationship = self._save(existing, venue_id, worker_id, relationship_type, now, actor_user_id, default_role)
        self._record(existing, relationship, now, actor_user_id, reason)
        return relationship

    def record_first_shift(self, venue_id: str, worker_id: str, now: datetime) -> WorkerRelationship | None:
        if self._relationships.get_for_venue_worker(venue_id, worker_id) is not None:
            return None
        return self.establish(
            venue_id,
            worker_id,
            "one_off",
            now,
            reason="Completed a shift at this venue.",
        )

    def promote_to_pool(
        self, venue_id: str, worker_id: str, now: datetime, actor_user_id: str
    ) -> WorkerRelationship:
        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is None:
            raise NotFoundError("This worker has not worked at your venue yet.")
        if existing.status == "active" and existing.relationship_type in EMPLOYED_TYPES:
            raise ValidationError("This worker is already employed by your venue.")
        profile = self._workers.get(worker_id)
        if profile is None:
            raise NotFoundError(f"Worker {worker_id} was not found.")
        if not profile.allow_venue_recontact:
            raise ValidationError("This worker has turned off contact from venues they have worked for.")
        return self.establish(
            venue_id,
            worker_id,
            "pool",
            now,
            actor_user_id=actor_user_id,
            reason="Added to the venue pool.",
        )

    def remove_from_pool(
        self, venue_id: str, worker_id: str, now: datetime, actor_user_id: str
    ) -> WorkerRelationship:
        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is None or existing.relationship_type != "pool":
            raise NotFoundError("This worker is not in your pool.")
        return self.establish(
            venue_id,
            worker_id,
            "one_off",
            now,
            actor_user_id=actor_user_id,
            reason="Removed from the venue pool.",
        )

    def invite_to_employment(
        self,
        venue_id: str,
        worker_id: str,
        relationship_type: str,
        now: datetime,
        actor_user_id: str,
        default_role: str | None = None,
    ) -> WorkerRelationship:
        if relationship_type not in EMPLOYED_TYPES:
            raise ValidationError("Only permanent, part-time and bank staff are invited to employment.")
        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is not None and existing.status == "active" and existing.relationship_type in EMPLOYED_TYPES:
            raise ValidationError("This worker is already employed by your venue.")
        if existing is not None and self._pending_target(existing) is not None:
            raise ValidationError("This worker already has an invitation waiting.")

        if existing is None or existing.status == "ended":
            relationship = self._save(
                existing, venue_id, worker_id, "one_off", now, actor_user_id, default_role, status="invited"
            )
        else:
            relationship = self._relationships.save(
                replace(
                    existing,
                    status="invited",
                    updated_at=now,
                    default_role=default_role or existing.default_role,
                )
            )
        self._transitions.record(
            RelationshipTransition(
                transition_id=str(uuid4()),
                relationship_id=relationship.relationship_id,
                from_relationship_type=existing.relationship_type if existing else None,
                from_status=existing.status if existing else None,
                to_relationship_type=relationship_type,
                to_status="invited",
                occurred_at=now,
                actor_user_id=actor_user_id,
                reason="Invited to join the team.",
            )
        )
        return relationship

    def respond_to_invitation(
        self, relationship_id: str, worker_id: str, accepted: bool, now: datetime
    ) -> WorkerRelationship:
        existing = self._relationships.get(relationship_id)
        if existing is None or existing.worker_id != worker_id:
            raise NotFoundError("That invitation was not found.")
        target = self._pending_target(existing)
        if target is None:
            raise ValidationError("That invitation has already been answered.")

        invite = self._latest_transition(existing.relationship_id)
        if accepted:
            relationship = self._save(
                existing, existing.venue_id, worker_id, target, now, None, existing.default_role, status="active"
            )
            self._record(existing, relationship, now, None, "Invitation accepted.")
            return relationship

        prior_type = (
            invite.from_relationship_type
            if invite and invite.from_relationship_type
            else existing.relationship_type
        )
        prior_status = invite.from_status if invite and invite.from_status else "ended"
        relationship = self._save(
            existing,
            existing.venue_id,
            worker_id,
            prior_type,
            now,
            None,
            existing.default_role,
            status=prior_status,
            end_date=now if prior_status == "ended" else None,
        )
        self._record(existing, relationship, now, None, "Invitation declined.")
        return relationship

    def set_terms(
        self,
        venue_id: str,
        worker_id: str,
        now: datetime,
        agreed_rate=None,
        contracted_hours_per_week=None,
        default_role: str | None = None,
    ) -> WorkerRelationship:
        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is None or existing.status != "active" or existing.relationship_type not in EMPLOYED_TYPES:
            raise ValidationError("Terms can only be set on active employed staff.")
        return self._relationships.save(
            replace(
                existing,
                agreed_rate=agreed_rate if agreed_rate is not None else existing.agreed_rate,
                contracted_hours_per_week=(
                    contracted_hours_per_week
                    if contracted_hours_per_week is not None
                    else existing.contracted_hours_per_week
                ),
                default_role=default_role or existing.default_role,
                updated_at=now,
            )
        )

    def _pending_target(self, relationship: WorkerRelationship) -> str | None:
        if relationship.status != "invited":
            return None
        latest = self._latest_transition(relationship.relationship_id)
        if latest is not None and latest.to_status == "invited":
            return latest.to_relationship_type
        return relationship.relationship_type

    def _latest_transition(self, relationship_id: str) -> RelationshipTransition | None:
        recorded = self._transitions.list_for_relationship(relationship_id)
        return recorded[-1] if recorded else None

    def list_invitations(self, worker_id: str) -> list[PendingInvitation]:
        pending = []
        for item in self._relationships.list_for_worker(worker_id):
            target = self._pending_target(item)
            if target is not None:
                pending.append(PendingInvitation(relationship=item, target_type=target))
        return pending

    def end(
        self, venue_id: str, worker_id: str, now: datetime, actor_user_id: str, reason: str | None = None
    ) -> WorkerRelationship:
        existing = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is None:
            raise NotFoundError("This worker has no relationship with your venue.")
        relationship = self._save(
            existing,
            venue_id,
            worker_id,
            existing.relationship_type,
            now,
            actor_user_id,
            existing.default_role,
            status="ended",
            end_date=now,
        )
        self._record(existing, relationship, now, actor_user_id, reason or "Relationship ended.")
        return relationship

    def _save(self, existing, venue_id, worker_id, relationship_type, now, actor_user_id, default_role, status="active", end_date=None):
        return save_relationship(
            self._relationships, existing, venue_id, worker_id, relationship_type, now,
            actor_user_id, default_role, status=status, end_date=end_date,
        )

    def _record(self, previous, current, now, actor_user_id, reason):
        record_transition(self._transitions, previous, current, now, actor_user_id, reason)
