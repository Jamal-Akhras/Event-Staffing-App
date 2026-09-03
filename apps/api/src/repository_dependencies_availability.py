from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.repositories.availability_repository import (
    AvailabilityExceptionRepository,
    AvailabilityRuleRepository,
    TimeOffRepository,
)
from apps.api.src.repositories.in_memory_availability_repository import (
    InMemoryAvailabilityExceptionRepository,
    InMemoryAvailabilityRuleRepository,
    InMemoryTimeOffRepository,
)
from apps.api.src.repositories.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityExceptionRepository,
    SqlAlchemyAvailabilityRuleRepository,
    SqlAlchemyTimeOffRepository,
)
from apps.api.src.repository_dependencies import get_request_session

_AVAILABILITY_RULES = InMemoryAvailabilityRuleRepository()
_AVAILABILITY_EXCEPTIONS = InMemoryAvailabilityExceptionRepository()
_TIME_OFF = InMemoryTimeOffRepository()


def _session(value: Session | None) -> Session:
    if value is None:
        raise RuntimeError("A database-backed repository requires a request session.")
    return value


def get_availability_rule_repo(
    session: Session | None = Depends(get_request_session),
) -> AvailabilityRuleRepository:
    if use_in_memory_repositories():
        return _AVAILABILITY_RULES
    return SqlAlchemyAvailabilityRuleRepository(_session(session))


def get_availability_exception_repo(
    session: Session | None = Depends(get_request_session),
) -> AvailabilityExceptionRepository:
    if use_in_memory_repositories():
        return _AVAILABILITY_EXCEPTIONS
    return SqlAlchemyAvailabilityExceptionRepository(_session(session))


def get_time_off_repo(
    session: Session | None = Depends(get_request_session),
) -> TimeOffRepository:
    if use_in_memory_repositories():
        return _TIME_OFF
    return SqlAlchemyTimeOffRepository(_session(session))
