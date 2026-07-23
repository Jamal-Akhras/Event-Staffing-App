from __future__ import annotations

from apps.api.src.helpers import _now
from apps.api.src.models.message import Message
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas import MessageSendRequest
from apps.api.src.services.errors import ForbiddenError, NotFoundError, ValidationError

ActorValue = str


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        shift_repo: ShiftRepository,
        application_repo: ApplicationRepository,
        booking_repo: BookingRepository,
    ) -> None:
        self._messages = message_repo
        self._shifts = shift_repo
        self._applications = application_repo
        self._bookings = booking_repo

    def send_message(
        self,
        shift_id: str,
        request: MessageSendRequest,
        actor_role: ActorValue,
        actor_user_id: str,
    ) -> Message:
        shift = self._get_shift(shift_id)
        if not request.application_id and not request.booking_id:
            raise ValidationError("Either application_id or booking_id must be provided")
        self._require_thread_access(actor_role, actor_user_id, shift, request.application_id, request.booking_id)

        now = _now()
        message = Message(
            message_id=f"msg_{now.strftime('%Y%m%d%H%M%S%f')}",
            shift_id=shift_id,
            application_id=request.application_id,
            booking_id=request.booking_id,
            sender_id=actor_user_id,
            sender_role=actor_role,
            content=request.content,
            read_at=None,
            created_at=now,
        )
        return self._messages.save(message)

    def list_messages(
        self,
        shift_id: str,
        actor_role: ActorValue,
        actor_user_id: str,
        application_id: str | None = None,
        booking_id: str | None = None,
    ) -> list[Message]:
        shift = self._get_shift(shift_id)
        self._require_thread_access(actor_role, actor_user_id, shift, application_id, booking_id)
        if booking_id:
            return self._messages.list_by_booking(booking_id)
        if application_id:
            return self._messages.list_by_application(application_id)
        return self._messages.list_by_shift(shift_id)

    def mark_as_read(self, message_id: str, actor_role: ActorValue, actor_user_id: str) -> None:
        message = self._messages.get(message_id)
        if message is None:
            raise NotFoundError(f"Message not found: {message_id}")
        shift = self._get_shift(message.shift_id)
        self._require_thread_access(
            actor_role,
            actor_user_id,
            shift,
            message.application_id,
            message.booking_id,
        )
        if not self._messages.mark_as_read(message_id):
            raise NotFoundError(f"Message not found: {message_id}")

    def _get_shift(self, shift_id: str) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is None:
            raise NotFoundError(f"Shift not found: {shift_id}")
        return shift

    def _require_thread_access(
        self,
        actor_role: ActorValue,
        actor_user_id: str,
        shift: Shift,
        application_id: str | None,
        booking_id: str | None,
    ) -> None:
        application_worker_id = self._application_worker_id(application_id, shift.shift_id) if application_id else None
        booking_worker_id = self._booking_worker_id(booking_id, shift.shift_id) if booking_id else None
        if actor_role == "operator":
            if shift.operator_id != actor_user_id:
                raise ForbiddenError("Operator can only access their own shift messages.")
            return
        if actor_role == "worker":
            if application_worker_id == actor_user_id:
                return
            if booking_worker_id == actor_user_id:
                return
            raise ForbiddenError("Worker can only access their own message threads.")
        raise ForbiddenError("Actor is not allowed to access messages.")

    def _application_worker_id(self, application_id: str, shift_id: str) -> str:
        application = self._applications.get(application_id)
        if application is None or application.shift_id != shift_id:
            raise NotFoundError("Application not found.")
        return application.worker_id

    def _booking_worker_id(self, booking_id: str, shift_id: str) -> str:
        booking = self._bookings.get(booking_id)
        if booking is None or booking.shift_id != shift_id:
            raise NotFoundError("Booking not found.")
        return booking.worker_id
