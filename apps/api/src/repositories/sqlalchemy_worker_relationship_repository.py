from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.workforce_models import RelationshipTransitionModel, WorkerRelationshipModel
from apps.api.src.models.worker_relationship import RelationshipTransition, WorkerRelationship

_RELATIONSHIP_FIELDS = tuple(WorkerRelationship.__dataclass_fields__)
_TRANSITION_FIELDS = tuple(RelationshipTransition.__dataclass_fields__)


def _to_relationship(row: WorkerRelationshipModel) -> WorkerRelationship:
    return WorkerRelationship(**{name: getattr(row, name) for name in _RELATIONSHIP_FIELDS})


def _to_transition(row: RelationshipTransitionModel) -> RelationshipTransition:
    return RelationshipTransition(**{name: getattr(row, name) for name in _TRANSITION_FIELDS})


class SqlAlchemyWorkerRelationshipRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, relationship: WorkerRelationship) -> WorkerRelationship:
        values = {name: getattr(relationship, name) for name in _RELATIONSHIP_FIELDS}
        row = self._session.get(WorkerRelationshipModel, relationship.relationship_id)
        if row is None:
            self._session.add(WorkerRelationshipModel(**values))
        else:
            for name, value in values.items():
                setattr(row, name, value)
        self._session.flush()
        return relationship

    def get(self, relationship_id: str) -> WorkerRelationship | None:
        row = self._session.get(WorkerRelationshipModel, relationship_id)
        return _to_relationship(row) if row else None

    def get_for_venue_worker(self, venue_id: str, worker_id: str) -> WorkerRelationship | None:
        row = self._session.execute(
            select(WorkerRelationshipModel).where(
                WorkerRelationshipModel.venue_id == venue_id,
                WorkerRelationshipModel.worker_id == worker_id,
            )
        ).scalar_one_or_none()
        return _to_relationship(row) if row else None

    def list_for_venue(self, venue_id: str, status: str | None = None) -> list[WorkerRelationship]:
        query = select(WorkerRelationshipModel).where(WorkerRelationshipModel.venue_id == venue_id)
        if status is not None:
            query = query.where(WorkerRelationshipModel.status == status)
        rows = self._session.execute(query.order_by(WorkerRelationshipModel.created_at)).scalars().all()
        return [_to_relationship(row) for row in rows]

    def list_for_worker(self, worker_id: str) -> list[WorkerRelationship]:
        rows = self._session.execute(
            select(WorkerRelationshipModel)
            .where(WorkerRelationshipModel.worker_id == worker_id)
            .order_by(WorkerRelationshipModel.created_at)
        ).scalars().all()
        return [_to_relationship(row) for row in rows]


class SqlAlchemyRelationshipTransitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, transition: RelationshipTransition) -> RelationshipTransition:
        self._session.add(
            RelationshipTransitionModel(**{name: getattr(transition, name) for name in _TRANSITION_FIELDS})
        )
        self._session.flush()
        return transition

    def list_for_relationship(self, relationship_id: str) -> list[RelationshipTransition]:
        rows = self._session.execute(
            select(RelationshipTransitionModel)
            .where(RelationshipTransitionModel.relationship_id == relationship_id)
            .order_by(RelationshipTransitionModel.occurred_at)
        ).scalars().all()
        return [_to_transition(row) for row in rows]
