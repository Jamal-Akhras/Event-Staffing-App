from __future__ import annotations

from apps.api.src.models.worker_relationship import RelationshipTransition, WorkerRelationship


class InMemoryWorkerRelationshipRepository:
    def __init__(self) -> None:
        self._relationships: dict[str, WorkerRelationship] = {}

    def save(self, relationship: WorkerRelationship) -> WorkerRelationship:
        self._relationships[relationship.relationship_id] = relationship
        return relationship

    def get(self, relationship_id: str) -> WorkerRelationship | None:
        return self._relationships.get(relationship_id)

    def get_for_venue_worker(self, venue_id: str, worker_id: str) -> WorkerRelationship | None:
        for relationship in self._relationships.values():
            if relationship.venue_id == venue_id and relationship.worker_id == worker_id:
                return relationship
        return None

    def list_for_venue(self, venue_id: str, status: str | None = None) -> list[WorkerRelationship]:
        return sorted(
            (
                relationship
                for relationship in self._relationships.values()
                if relationship.venue_id == venue_id and (status is None or relationship.status == status)
            ),
            key=lambda relationship: relationship.created_at,
        )

    def list_for_worker(self, worker_id: str) -> list[WorkerRelationship]:
        return sorted(
            (
                relationship
                for relationship in self._relationships.values()
                if relationship.worker_id == worker_id
            ),
            key=lambda relationship: relationship.created_at,
        )

    def clear(self) -> None:
        self._relationships.clear()


class InMemoryRelationshipTransitionRepository:
    def __init__(self) -> None:
        self._transitions: list[RelationshipTransition] = []

    def record(self, transition: RelationshipTransition) -> RelationshipTransition:
        self._transitions.append(transition)
        return transition

    def list_for_relationship(self, relationship_id: str) -> list[RelationshipTransition]:
        return sorted(
            (
                transition
                for transition in self._transitions
                if transition.relationship_id == relationship_id
            ),
            key=lambda transition: transition.occurred_at,
        )

    def clear(self) -> None:
        self._transitions.clear()
