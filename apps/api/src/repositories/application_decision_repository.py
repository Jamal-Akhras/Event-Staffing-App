from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from packages.domain.src.booking import Booking


@dataclass(frozen=True)
class ApplicationApprovalResult:
    application: Application
    booking: Booking
    shift: Shift


class ApplicationDecisionError(Exception):
    pass


class ApplicationDecisionNotFoundError(ApplicationDecisionError):
    pass


class ApplicationAlreadyDecidedError(ApplicationDecisionError):
    pass


class ShiftAlreadyFullError(ApplicationDecisionError):
    pass


class ApplicationDecisionConflictError(ApplicationDecisionError):
    pass


class ApplicationDecisionRepository(Protocol):
    def approve(
        self,
        application_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
    ) -> ApplicationApprovalResult:
        ...

    def reject(self, application_id: str, now: datetime) -> Application:
        ...
