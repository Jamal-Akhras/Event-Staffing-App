from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import Lock

from apps.api.src.models.application import Application
from apps.api.src.repositories.booking_allocator import (
    AllocationTargetMissingError,
    ShiftFullError,
)
from apps.api.src.repositories.application_decision_repository import (
    ApplicationAlreadyDecidedError,
    ApplicationApprovalResult,
    ApplicationDecisionNotFoundError,
    ShiftAlreadyFullError,
)
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class InMemoryApplicationDecisionRepository:
    def __init__(
        self,
        applications: ApplicationRepository,
        bookings: BookingRepository,
        shifts: ShiftRepository,
    ) -> None:
        self._applications = applications
        self._bookings = bookings
        self._shifts = shifts
        self._lock = Lock()

    def approve(
        self,
        application_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
    ) -> ApplicationApprovalResult:
        from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator

        with self._lock:
            application = self._get_applied_application(application_id)
            try:
                allocated = InMemoryBookingAllocator(self._bookings, self._shifts).allocate(
                    application.shift_id,
                    application.worker_id,
                    now,
                    booking_id,
                    attendance_mode=attendance_mode,
                )
            except AllocationTargetMissingError as exc:
                raise ApplicationDecisionNotFoundError("Shift not found.") from exc
            except ShiftFullError as exc:
                raise ShiftAlreadyFullError("Shift is already fully staffed.") from exc

            application = replace(
                application,
                status="approved",
                decided_at=now,
                booking_id=booking_id,
            )
            application = self._applications.save(application)
            return ApplicationApprovalResult(
                application=application, booking=allocated.booking, shift=allocated.shift
            )

    def reject(self, application_id: str, now: datetime) -> Application:
        with self._lock:
            application = self._get_applied_application(application_id)
            return self._applications.save(
                replace(application, status="rejected", decided_at=now),
            )

    def _get_applied_application(self, application_id: str) -> Application:
        application = self._applications.get(application_id)
        if application is None:
            raise ApplicationDecisionNotFoundError("Application not found.")
        if application.status != "applied":
            raise ApplicationAlreadyDecidedError("Application already decided.")
        return application
