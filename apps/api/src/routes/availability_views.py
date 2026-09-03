from __future__ import annotations

from dataclasses import asdict

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityRule,
    TimeOffRequest,
)
from apps.api.src.schemas_availability import (
    AvailabilityExceptionResponse,
    AvailabilityRuleResponse,
    TimeOffResponse,
)


def rule_view(rule: AvailabilityRule) -> AvailabilityRuleResponse:
    return AvailabilityRuleResponse(**asdict(rule))


def exception_view(exception: AvailabilityException) -> AvailabilityExceptionResponse:
    return AvailabilityExceptionResponse(**asdict(exception))


def time_off_view(request: TimeOffRequest) -> TimeOffResponse:
    return TimeOffResponse(**asdict(request))
