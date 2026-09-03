from __future__ import annotations

from datetime import datetime

from apps.api.src.models.availability import TimeOffStatus
from apps.api.src.repositories.availability_repository import TimeOffRepository
from apps.api.src.services.errors import ConflictError


class ApprovedTimeOffConflictError(ConflictError):
    def __init__(self, request_ids: tuple[str, ...]) -> None:
        self.request_ids = request_ids
        joined_ids = ", ".join(request_ids)
        super().__init__(f"Worker has approved time off that overlaps this shift: {joined_ids}.")


class AvailabilityGate:
    def __init__(self, time_off: TimeOffRepository) -> None:
        self._time_off = time_off

    def ensure_no_approved_time_off(
        self,
        worker_id: str,
        venue_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        conflicts = self._time_off.list_overlapping_workers(
            [worker_id],
            start_time,
            end_time,
            venue_id=venue_id,
            statuses=(TimeOffStatus.APPROVED,),
        )
        if conflicts:
            request_ids = tuple(sorted(request.request_id for request in conflicts))
            raise ApprovedTimeOffConflictError(request_ids)
