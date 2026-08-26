from __future__ import annotations

from apps.api.src.auth.actor import ActorContext, ActorRole
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.services.errors import ForbiddenError, NotFoundError


def require_report_subject_access(
    actor: ActorContext,
    subject_type: str,
    subject_id: str,
    applications: ApplicationRepository,
    bookings: BookingRepository,
    messages: MessageRepository,
    organisations: OrganisationRepository,
    shifts: ShiftRepository,
) -> None:
    if subject_type == "venue":
        if organisations.get_venue(subject_id) is None:
            raise NotFoundError("Venue not found.")
        return
    if subject_type == "shift":
        _require_shift_access(actor, subject_id, applications, bookings, shifts)
        return
    if subject_type == "application":
        application = applications.get(subject_id)
        if application is None:
            raise NotFoundError("Application not found.")
        _require_participant(actor, application.worker_id, application.shift_id, shifts)
        return
    if subject_type == "booking":
        booking = bookings.get(subject_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        _require_participant(actor, booking.worker_id, booking.shift_id, shifts)
        return
    if subject_type == "message":
        message = messages.get(subject_id)
        if message is None:
            raise NotFoundError("Message not found.")
        if message.application_id:
            application = applications.get(message.application_id)
            if application is None:
                raise NotFoundError("Application not found.")
            _require_participant(actor, application.worker_id, application.shift_id, shifts)
            return
        if message.booking_id:
            booking = bookings.get(message.booking_id)
            if booking is None:
                raise NotFoundError("Booking not found.")
            _require_participant(actor, booking.worker_id, booking.shift_id, shifts)
            return
    raise NotFoundError("Report subject not found.")


def _require_shift_access(
    actor: ActorContext,
    shift_id: str,
    applications: ApplicationRepository,
    bookings: BookingRepository,
    shifts: ShiftRepository,
) -> None:
    shift = shifts.get(shift_id)
    if shift is None:
        raise NotFoundError("Shift not found.")
    if actor.role == ActorRole.OPERATOR and shift.account_id == actor.account_id:
        return
    worker_id = actor.effective_worker_id
    if actor.role == ActorRole.WORKER:
        if shift.status == "open" or applications.find_by_worker_and_shift(worker_id, shift_id):
            return
        if any(item.worker_id == worker_id for item in bookings.list_by_shift(shift_id)):
            return
    raise ForbiddenError("You can only report marketplace activity visible to you.")


def _require_participant(
    actor: ActorContext,
    worker_id: str,
    shift_id: str,
    shifts: ShiftRepository,
) -> None:
    if actor.role == ActorRole.WORKER:
        if actor.effective_worker_id == worker_id:
            return
        raise ForbiddenError("You can only report your own marketplace activity.")
    shift = shifts.get(shift_id)
    if actor.role == ActorRole.OPERATOR and shift and shift.account_id == actor.account_id:
        return
    raise ForbiddenError("You can only report activity for your active venue.")
