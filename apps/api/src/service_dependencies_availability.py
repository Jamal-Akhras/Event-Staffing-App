from __future__ import annotations

from fastapi import Depends

from apps.api.src.repository_dependencies import get_booking_repo
from apps.api.src.repository_dependencies_availability import (
    get_availability_exception_repo,
    get_availability_rule_repo,
    get_time_off_repo,
)
from apps.api.src.repository_dependencies_workforce import get_worker_relationship_repo
from apps.api.src.repositories.availability_repository import (
    AvailabilityExceptionRepository,
    AvailabilityRuleRepository,
    TimeOffRepository,
)
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.availability_management_service import AvailabilityManagementService
from apps.api.src.services.availability_service import AvailabilityService


def get_availability_service(
    rules: AvailabilityRuleRepository = Depends(get_availability_rule_repo),
    exceptions: AvailabilityExceptionRepository = Depends(get_availability_exception_repo),
    time_off: TimeOffRepository = Depends(get_time_off_repo),
    bookings: BookingRepository = Depends(get_booking_repo),
) -> AvailabilityService:
    return AvailabilityService(rules, exceptions, time_off, bookings)


def get_availability_management_service(
    rules: AvailabilityRuleRepository = Depends(get_availability_rule_repo),
    exceptions: AvailabilityExceptionRepository = Depends(get_availability_exception_repo),
    time_off: TimeOffRepository = Depends(get_time_off_repo),
    relationships: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    bookings: BookingRepository = Depends(get_booking_repo),
) -> AvailabilityManagementService:
    return AvailabilityManagementService(rules, exceptions, time_off, relationships, bookings)
