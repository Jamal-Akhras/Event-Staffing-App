from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from apps.api.src.auth.actor import ActorContext, ActorRole
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.application import Application
from apps.api.src.models.message import Message
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas import MessageSendRequest
from apps.api.src.services.errors import ForbiddenError, NotFoundError, ValidationError
from apps.api.src.services.outbox_publisher import OutboxPublisher
from packages.domain.src.booking import Booking

NOTIFICATION_BODY_LIMIT = 140
THREAD_READ_WINDOW = 500


@dataclass(frozen=True)
class MessageThread:
    shift: Shift
    application: Application | None
    booking: Booking | None
    worker_id: str


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        shift_repo: ShiftRepository,
        application_repo: ApplicationRepository,
        booking_repo: BookingRepository,
        outbox: OutboxPublisher,
    ) -> None:
        self._messages = message_repo
        self._shifts = shift_repo
        self._applications = application_repo
        self._bookings = booking_repo
        self._outbox = outbox

    def send_message(self, shift_id: str, request: MessageSendRequest, actor: ActorContext) -> Message:
        thread = self._open_thread(shift_id, actor, request.application_id, request.booking_id)
        message = Message(
            message_id=f"msg_{uuid4().hex}",
            shift_id=shift_id,
            application_id=thread.application.application_id if thread.application else None,
            booking_id=thread.booking.booking_id if thread.booking else None,
            sender_id=_sender_id(actor),
            sender_role=actor.role.value,
            content=request.content,
            read_at=None,
            created_at=utc_now(),
        )
        saved = self._messages.save(message)
        self._publish_message(saved, thread, actor)
        return saved

    def list_messages(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None = None,
        booking_id: str | None = None,
        limit: int = 100,
    ) -> list[Message]:
        thread = self._open_thread(shift_id, actor, application_id, booking_id)
        return self._thread_messages(thread, limit)

    def mark_thread_read(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None = None,
        booking_id: str | None = None,
    ) -> int:
        thread = self._open_thread(shift_id, actor, application_id, booking_id)
        marked = 0
        for message in self._thread_messages(thread, THREAD_READ_WINDOW):
            if message.read_at is None and message.sender_role != actor.role.value:
                if self._messages.mark_as_read(message.message_id):
                    marked += 1
        return marked

    def mark_as_read(self, message_id: str, actor: ActorContext) -> None:
        message = self._messages.get(message_id)
        if message is None:
            raise NotFoundError(f"Message not found: {message_id}")
        self._open_thread(message.shift_id, actor, message.application_id, message.booking_id)
        if message.sender_role == actor.role.value:
            raise ForbiddenError("Only the recipient can mark a message as read.")
        if not self._messages.mark_as_read(message_id):
            raise NotFoundError(f"Message not found: {message_id}")

    def _open_thread(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None,
        booking_id: str | None,
    ) -> MessageThread:
        shift = self._shifts.get(shift_id)
        if shift is None:
            raise NotFoundError(f"Shift not found: {shift_id}")
        if not application_id and not booking_id:
            raise ValidationError("Either application_id or booking_id must be provided")
        thread = self._resolve_thread(shift, application_id, booking_id)
        self._require_thread_access(actor, thread)
        return thread

    def _resolve_thread(self, shift: Shift, application_id: str | None, booking_id: str | None) -> MessageThread:
        application = self._get_application(application_id, shift.shift_id) if application_id else None
        booking = self._get_booking(booking_id, shift.shift_id) if booking_id else None
        if application is not None and booking is None and application.booking_id:
            booking = self._bookings.get(application.booking_id)
        if booking is not None and application is None:
            application = self._applications.find_by_worker_and_shift(booking.worker_id, shift.shift_id)
        if application is not None and booking is not None and application.worker_id != booking.worker_id:
            raise ValidationError("Application and booking belong to different workers.")
        worker_id = application.worker_id if application is not None else booking.worker_id
        return MessageThread(shift, application, booking, worker_id)

    def _get_application(self, application_id: str, shift_id: str) -> Application:
        application = self._applications.get(application_id)
        if application is None or application.shift_id != shift_id:
            raise NotFoundError("Application not found.")
        return application

    def _get_booking(self, booking_id: str, shift_id: str) -> Booking:
        booking = self._bookings.get(booking_id)
        if booking is None or booking.shift_id != shift_id:
            raise NotFoundError("Booking not found.")
        return booking

    def _require_thread_access(self, actor: ActorContext, thread: MessageThread) -> None:
        if actor.role == ActorRole.OPERATOR:
            if not _operator_owns_shift(actor, thread.shift):
                raise ForbiddenError("Operator can only access their own shift messages.")
            return
        if actor.role == ActorRole.WORKER and thread.worker_id == actor.effective_worker_id:
            return
        raise ForbiddenError("Worker can only access their own message threads.")

    def _thread_messages(self, thread: MessageThread, limit: int) -> list[Message]:
        by_id: dict[str, Message] = {}
        if thread.application is not None:
            for message in self._messages.list_by_application(thread.application.application_id, limit):
                by_id[message.message_id] = message
        if thread.booking is not None:
            for message in self._messages.list_by_booking(thread.booking.booking_id, limit):
                by_id[message.message_id] = message
        ordered = sorted(by_id.values(), key=lambda item: (item.created_at, item.message_id))
        return ordered[-limit:]

    def _publish_message(self, message: Message, thread: MessageThread, actor: ActorContext) -> None:
        if actor.role == ActorRole.WORKER:
            if not thread.shift.account_id:
                return
            recipient_kind, recipient_id = "venue", thread.shift.account_id
        else:
            recipient_kind, recipient_id = "worker", thread.worker_id
        if thread.application is not None:
            action_kind, action_entity_id = "messages", thread.application.application_id
        else:
            action_kind, action_entity_id = "booking", thread.booking.booking_id
        self._outbox.publish_notification(
            event_type="message.created",
            aggregate_type="message",
            aggregate_id=message.message_id,
            recipient_kind=recipient_kind,
            recipient_id=recipient_id,
            category="messages",
            title="New message",
            body=_preview(message.content),
            action_kind=action_kind,
            action_entity_id=action_entity_id,
        )


def _sender_id(actor: ActorContext) -> str:
    return actor.effective_worker_id if actor.role == ActorRole.WORKER else actor.user_id


def _operator_owns_shift(actor: ActorContext, shift: Shift) -> bool:
    if shift.account_id and actor.account_id:
        return shift.account_id == actor.account_id
    return shift.operator_id == actor.user_id


def _preview(content: str) -> str:
    if len(content) <= NOTIFICATION_BODY_LIMIT:
        return content
    return content[: NOTIFICATION_BODY_LIMIT - 1].rstrip() + "…"
