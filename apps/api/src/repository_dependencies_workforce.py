from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.repositories.in_memory_venue_join_code_repository import InMemoryVenueJoinCodeRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryRelationshipTransitionRepository,
    InMemoryWorkerRelationshipRepository,
)  # noqa: F401
from apps.api.src.repositories.sqlalchemy_venue_join_code_repository import SqlAlchemyVenueJoinCodeRepository
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyRelationshipTransitionRepository,
    SqlAlchemyWorkerRelationshipRepository,
)
from apps.api.src.repositories.venue_join_code_repository import VenueJoinCodeRepository
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)
from apps.api.src.repository_dependencies import _RELATIONSHIPS, get_request_session

_RELATIONSHIP_TRANSITIONS = InMemoryRelationshipTransitionRepository()
_JOIN_CODES = InMemoryVenueJoinCodeRepository()


def _session(value: Session | None) -> Session:
    if value is None:
        raise RuntimeError("A database-backed repository requires a request session.")
    return value


def get_worker_relationship_repo(
    session: Session | None = Depends(get_request_session),
) -> WorkerRelationshipRepository:
    if use_in_memory_repositories():
        return _RELATIONSHIPS
    return SqlAlchemyWorkerRelationshipRepository(_session(session))


def get_relationship_transition_repo(
    session: Session | None = Depends(get_request_session),
) -> RelationshipTransitionRepository:
    if use_in_memory_repositories():
        return _RELATIONSHIP_TRANSITIONS
    return SqlAlchemyRelationshipTransitionRepository(_session(session))


def get_venue_join_code_repo(
    session: Session | None = Depends(get_request_session),
) -> VenueJoinCodeRepository:
    if use_in_memory_repositories():
        return _JOIN_CODES
    return SqlAlchemyVenueJoinCodeRepository(_session(session))


def shared_worker_relationship_repository() -> InMemoryWorkerRelationshipRepository:
    return _RELATIONSHIPS


def shared_relationship_transition_repository() -> InMemoryRelationshipTransitionRepository:
    return _RELATIONSHIP_TRANSITIONS


def shared_venue_join_code_repository() -> InMemoryVenueJoinCodeRepository:
    return _JOIN_CODES
