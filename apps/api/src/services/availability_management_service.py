from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityExceptionKind,
    AvailabilityRule,
    TimeOffRequest,
    TimeOffStatus,
)
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.availability_repository import (
    AvailabilityExceptionRepository,
    AvailabilityRuleRepository,
    TimeOffRepository,
)
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError


class BookingConflictError(ConflictError):
    def __init__(self, booking_ids: tuple[str, ...]) -> None:
        self.booking_ids = booking_ids
        super().__init__(f"Time off overlaps confirmed work: {', '.join(booking_ids)}.")


class AvailabilityManagementService:
    def __init__(
        self,
        rules: AvailabilityRuleRepository,
        exceptions: AvailabilityExceptionRepository,
        time_off: TimeOffRepository,
        relationships: WorkerRelationshipRepository,
        bookings: BookingRepository,
    ) -> None:
        self._rules = rules
        self._exceptions = exceptions
        self._time_off = time_off
        self._relationships = relationships
        self._bookings = bookings

    def list_rules(self, worker_id: str) -> list[AvailabilityRule]:
        return self._rules.list_for_worker(worker_id)

    def replace_rules(self, worker_id: str, inputs: list[dict], now: datetime) -> list[AvailabilityRule]:
        rules = [
            AvailabilityRule(
                rule_id=str(uuid4()),
                worker_id=worker_id,
                created_at=now,
                updated_at=now,
                **item,
            )
            for item in inputs
        ]
        return self._rules.replace_for_worker(worker_id, rules)

    def list_exceptions(self, worker_id: str) -> list[AvailabilityException]:
        return self._exceptions.list_for_worker(worker_id)

    def create_exception(
        self,
        worker_id: str,
        kind: AvailabilityExceptionKind,
        start_time: datetime,
        end_time: datetime,
        note: str | None,
        now: datetime,
    ) -> AvailabilityException:
        return self._exceptions.save(
            AvailabilityException(
                exception_id=str(uuid4()),
                worker_id=worker_id,
                kind=kind,
                start_time=start_time,
                end_time=end_time,
                note=note,
                created_at=now,
                updated_at=now,
            )
        )

    def delete_exception(self, worker_id: str, exception_id: str) -> AvailabilityException:
        exception = self._exceptions.get(exception_id)
        if exception is None or exception.worker_id != worker_id:
            raise NotFoundError("That availability exception was not found.")
        self._exceptions.delete(exception_id)
        return exception

    def list_time_off_for_worker(self, worker_id: str) -> list[TimeOffRequest]:
        return self._time_off.list_for_worker(worker_id)

    def request_time_off(
        self,
        worker_id: str,
        venue_id: str,
        start_time: datetime,
        end_time: datetime,
        reason: str,
        now: datetime,
    ) -> TimeOffRequest:
        relationship = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if (
            relationship is None
            or relationship.status != "active"
            or relationship.relationship_type not in EMPLOYED_TYPES
        ):
            raise ValidationError("Time off is only available for active employment at this venue.")
        if start_time <= now:
            raise ValidationError("Time off must start in the future.")
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise ValidationError("A reason is required for time off.")
        return self._time_off.save(
            TimeOffRequest(
                request_id=str(uuid4()),
                worker_id=worker_id,
                venue_id=venue_id,
                start_time=start_time,
                end_time=end_time,
                status=TimeOffStatus.PENDING,
                reason=cleaned_reason,
                created_at=now,
                updated_at=now,
            )
        )

    def withdraw_time_off(
        self, worker_id: str, request_id: str, now: datetime
    ) -> TimeOffRequest:
        request = self._owned_request(worker_id, request_id)
        if request.status != TimeOffStatus.PENDING:
            raise ConflictError("Only pending time off can be withdrawn.")
        return self._time_off.save(
            replace(request, status=TimeOffStatus.WITHDRAWN, updated_at=now)
        )

    def list_time_off_for_venue(
        self,
        venue_id: str,
        status: TimeOffStatus | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[TimeOffRequest]:
        if start_time is not None and end_time is not None and end_time <= start_time:
            raise ValidationError("starts_before must be after starts_from.")
        return self._time_off.list_for_venue(venue_id, status, start_time, end_time)

    def approve_time_off(
        self, venue_id: str, request_id: str, actor_user_id: str, now: datetime
    ) -> TimeOffRequest:
        request = self._venue_request(venue_id, request_id)
        self._require_pending(request)
        if request.end_time <= now:
            raise ConflictError("Time off that has ended cannot be approved.")
        conflicts = self._bookings.list_live_overlapping_for_worker(
            request.worker_id,
            max(request.start_time, now),
            request.end_time,
            venue_id=venue_id,
        )
        if conflicts:
            raise BookingConflictError(tuple(sorted(booking.booking_id for booking in conflicts)))
        return self._time_off.save(
            replace(
                request,
                status=TimeOffStatus.APPROVED,
                updated_at=now,
                decided_at=now,
                decided_by_user_id=actor_user_id,
            )
        )

    def decline_time_off(
        self, venue_id: str, request_id: str, actor_user_id: str, now: datetime
    ) -> TimeOffRequest:
        request = self._venue_request(venue_id, request_id)
        self._require_pending(request)
        return self._time_off.save(
            replace(
                request,
                status=TimeOffStatus.DECLINED,
                updated_at=now,
                decided_at=now,
                decided_by_user_id=actor_user_id,
            )
        )

    def _owned_request(self, worker_id: str, request_id: str) -> TimeOffRequest:
        request = self._time_off.get(request_id, for_update=True)
        if request is None or request.worker_id != worker_id:
            raise NotFoundError("That time-off request was not found.")
        return request

    def _venue_request(self, venue_id: str, request_id: str) -> TimeOffRequest:
        request = self._time_off.get(request_id, for_update=True)
        if request is None or request.venue_id != venue_id:
            raise NotFoundError("That time-off request was not found.")
        return request

    @staticmethod
    def _require_pending(request: TimeOffRequest) -> None:
        if request.status != TimeOffStatus.PENDING:
            raise ConflictError("That time-off request has already been decided.")
