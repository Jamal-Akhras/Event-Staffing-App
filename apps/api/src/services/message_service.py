from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from apps.api.src.auth.actor import ActorContext, ActorRole
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.application import Application
from apps.api.src.models.message import (
    Message,
    MessageReadReceipt,
    MessageThread,
    MessageThreadParticipant,
    MessageThreadView,
    MessageView,
)
from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES, WorkerRelationship
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository, LIVE_BOOKING_STATES
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.message_thread_repository import MessageThreadRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.schemas import MessageSendRequest
from apps.api.src.services.csv_safety import escape_csv_formula
from apps.api.src.services.errors import ForbiddenError, NotFoundError, ValidationError
from apps.api.src.services.outbox_publisher import OutboxPublisher
from packages.domain.src.booking import Booking

NOTIFICATION_BODY_LIMIT = 140
THREAD_READ_WINDOW = 500


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        thread_repo: MessageThreadRepository,
        shift_repo: ShiftRepository,
        application_repo: ApplicationRepository,
        booking_repo: BookingRepository,
        relationship_repo: WorkerRelationshipRepository,
        organisation_repo: OrganisationRepository,
        outbox: OutboxPublisher,
    ) -> None:
        self._messages = message_repo
        self._threads = thread_repo
        self._shifts = shift_repo
        self._applications = application_repo
        self._bookings = booking_repo
        self._relationships = relationship_repo
        self._organisations = organisation_repo
        self._outbox = outbox

    def send_message(self, shift_id: str, request: MessageSendRequest, actor: ActorContext) -> MessageView:
        thread = self._open_direct(shift_id, actor, request.application_id, request.booking_id)
        return self._send(thread, request.content, actor)

    def list_messages(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None = None,
        booking_id: str | None = None,
        limit: int = 100,
    ) -> list[MessageView]:
        thread = self._open_direct(shift_id, actor, application_id, booking_id)
        return self._views(thread, actor, limit)

    def group_thread(self, shift_id: str, actor: ActorContext, limit: int = 100) -> MessageThreadView:
        thread = self._open_group(shift_id, actor)
        return self._thread_view(thread, actor, limit)

    def send_group_message(self, shift_id: str, content: str, actor: ActorContext) -> MessageView:
        thread = self._open_group(shift_id, actor)
        self._require_can_post(thread, actor)
        return self._send(thread, content, actor)

    def employment_threads(self, actor: ActorContext) -> list[MessageThreadView]:
        relationships = self._employment_relationships(actor)
        return [self._thread_view(self._open_employment(row, actor), actor, 100) for row in relationships]

    def employment_thread(
        self, relationship_id: str, actor: ActorContext, limit: int = 100
    ) -> MessageThreadView:
        relationship = self._active_employment(relationship_id)
        return self._thread_view(self._open_employment(relationship, actor), actor, limit)

    def send_employment_message(
        self, relationship_id: str, content: str, actor: ActorContext
    ) -> MessageView:
        relationship = self._active_employment(relationship_id)
        thread = self._open_employment(relationship, actor)
        return self._send(thread, content, actor)

    def mark_direct_read(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None = None,
        booking_id: str | None = None,
    ) -> int:
        return self._mark_thread_read(
            self._open_direct(shift_id, actor, application_id, booking_id), actor
        )

    def mark_group_read(self, shift_id: str, actor: ActorContext) -> int:
        return self._mark_thread_read(self._open_group(shift_id, actor), actor)

    def mark_employment_read(self, relationship_id: str, actor: ActorContext) -> int:
        relationship = self._active_employment(relationship_id)
        return self._mark_thread_read(self._open_employment(relationship, actor), actor)

    def mark_as_read(self, message_id: str, actor: ActorContext) -> None:
        message = self._messages.get(message_id)
        if message is None:
            raise NotFoundError(f"Message not found: {message_id}")
        thread = self._thread_for_message(message, actor)
        if _sender_party(message) == _party(actor):
            raise ForbiddenError("Only another participant can mark this message as read.")
        self._save_receipt(message, actor)

    def export_csv(self, venue_id: str, month: str) -> str:
        try:
            since = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
        except ValueError as exc:
            raise ValidationError("month must use YYYY-MM format") from exc
        if since.month == 12:
            until = since.replace(year=since.year + 1, month=1)
        else:
            until = since.replace(month=since.month + 1)
        threads = self._threads.list_for_venue(venue_id)
        by_id = {thread.thread_id: thread for thread in threads}
        messages = self._messages.list_for_threads_between(list(by_id), since, until)
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["thread_kind", "shift_id", "role", "sender", "timestamp", "body"])
        for message in messages:
            thread = by_id[message.thread_id]
            writer.writerow(
                [
                    escape_csv_formula(thread.kind),
                    escape_csv_formula(thread.shift_id or ""),
                    escape_csv_formula(thread.role_snapshot or ""),
                    escape_csv_formula(message.sender_id),
                    message.created_at.isoformat(),
                    escape_csv_formula(message.content),
                ]
            )
        return buffer.getvalue()

    def _open_direct(
        self,
        shift_id: str,
        actor: ActorContext,
        application_id: str | None,
        booking_id: str | None,
    ) -> MessageThread:
        shift = self._shift(shift_id)
        if not application_id and not booking_id:
            raise ValidationError("Either application_id or booking_id must be provided")
        application, booking, worker_id = self._direct_context(shift_id, application_id, booking_id)
        self._require_direct_access(actor, shift, worker_id)
        thread = self._threads.get_direct(shift_id, worker_id)
        if thread is None:
            thread = self._new_thread(
                "direct", shift, worker_id=worker_id,
                application_id=application.application_id if application else None,
                booking_id=booking.booking_id if booking else None,
            )
            self._threads.save(thread)
            self._join_worker(thread, worker_id, thread.created_at)
        else:
            thread = self._enrich_direct(thread, application, booking)
        return thread

    def _open_group(self, shift_id: str, actor: ActorContext) -> MessageThread:
        shift = self._shift(shift_id)
        thread = self._threads.get_shift_group(shift_id)
        if thread is None:
            if actor.role != ActorRole.OPERATOR:
                raise NotFoundError("The venue has not opened this group thread.")
            self._require_operator_venue(actor, self._venue_id(shift))
            thread = self._new_thread("shift_group", shift)
            self._threads.save(thread)
        self._sync_group(thread, utc_now())
        self._require_read_access(thread, actor)
        return thread

    def _open_employment(
        self, relationship: WorkerRelationship, actor: ActorContext
    ) -> MessageThread:
        self._require_relationship_access(actor, relationship)
        thread = self._threads.get_employment(relationship.relationship_id)
        if thread is None:
            venue = self._venue(relationship.venue_id)
            thread = MessageThread(
                thread_id=_thread_id("employment", relationship.relationship_id),
                kind="employment",
                venue_id=relationship.venue_id,
                shift_id=None,
                application_id=None,
                booking_id=None,
                relationship_id=relationship.relationship_id,
                worker_id=relationship.worker_id,
                role_snapshot=relationship.default_role or relationship.relationship_type,
                venue_name_snapshot=venue.name,
                created_at=utc_now(),
            )
            self._threads.save(thread)
            self._join_worker(thread, relationship.worker_id, thread.created_at)
        return thread

    def _send(self, thread: MessageThread, content: str, actor: ActorContext) -> MessageView:
        self._require_can_post(thread, actor)
        message = self._messages.save(
            Message(
                message_id=f"msg_{uuid4().hex}",
                thread_id=thread.thread_id,
                sender_id=_party(actor)[1],
                sender_role=actor.role.value,
                content=content,
                created_at=utc_now(),
            )
        )
        self._publish_message(message, thread, actor)
        return self._view(message, thread, actor)

    def _mark_thread_read(self, thread: MessageThread, actor: ActorContext) -> int:
        marked = 0
        party = _party(actor)
        for message in self._visible_messages(thread, actor, THREAD_READ_WINDOW):
            if _sender_party(message) != party and self._threads.get_receipt(
                message.message_id, *party
            ) is None:
                self._save_receipt(message, actor)
                marked += 1
        return marked

    def _save_receipt(self, message: Message, actor: ActorContext) -> None:
        party_kind, party_id = _party(actor)
        self._threads.save_receipt(
            MessageReadReceipt(
                receipt_id=f"mrr_{uuid4().hex}",
                message_id=message.message_id,
                party_kind=party_kind,
                party_id=party_id,
                read_at=utc_now(),
            )
        )

    def _thread_for_message(self, message: Message, actor: ActorContext) -> MessageThread:
        thread = self._threads.get(message.thread_id)
        if thread is None:
            raise NotFoundError("Message thread not found.")
        if thread.kind == "shift_group":
            self._sync_group(thread, utc_now())
        self._require_read_access(thread, actor)
        if message not in self._visible_messages(thread, actor, THREAD_READ_WINDOW):
            raise ForbiddenError("That message is outside your participation interval.")
        return thread

    def _thread_view(self, thread: MessageThread, actor: ActorContext, limit: int) -> MessageThreadView:
        return MessageThreadView(
            thread=thread,
            messages=self._views(thread, actor, limit),
            can_post=self._can_post(thread, actor),
        )

    def _views(self, thread: MessageThread, actor: ActorContext, limit: int) -> list[MessageView]:
        return [self._view(message, thread, actor) for message in self._visible_messages(thread, actor, limit)]

    def _view(self, message: Message, thread: MessageThread, actor: ActorContext) -> MessageView:
        receipt = self._threads.get_receipt(message.message_id, *_party(actor))
        return MessageView(
            message_id=message.message_id,
            thread_id=thread.thread_id,
            thread_kind=thread.kind,
            shift_id=thread.shift_id,
            application_id=thread.application_id,
            booking_id=thread.booking_id,
            relationship_id=thread.relationship_id,
            sender_id=message.sender_id,
            sender_role=message.sender_role,
            content=message.content,
            read_at=receipt.read_at if receipt else None,
            created_at=message.created_at,
        )

    def _visible_messages(
        self, thread: MessageThread, actor: ActorContext, limit: int
    ) -> list[Message]:
        messages = self._messages.list_by_thread(thread.thread_id, limit)
        if thread.kind != "shift_group" or actor.role == ActorRole.OPERATOR:
            return messages
        intervals = self._worker_intervals(thread.thread_id, actor.effective_worker_id)
        return [
            message
            for message in messages
            if any(
                row.joined_at <= message.created_at
                and (row.left_at is None or message.created_at <= row.left_at)
                for row in intervals
            )
        ]

    def _sync_group(self, thread: MessageThread, now: datetime) -> None:
        live_workers = {
            booking.worker_id
            for booking in self._bookings.list_by_shift(thread.shift_id)
            if booking.state in LIVE_BOOKING_STATES
        }
        active = {
            row.party_id: row
            for row in self._threads.list_participants(thread.thread_id)
            if row.party_kind == "worker" and row.left_at is None
        }
        for worker_id in sorted(live_workers - set(active)):
            self._join_worker(thread, worker_id, now)
        for worker_id in sorted(set(active) - live_workers):
            self._threads.close_participant(active[worker_id].participant_id, now)

    def _join_worker(self, thread: MessageThread, worker_id: str, now: datetime) -> None:
        self._threads.save_participant(
            MessageThreadParticipant(
                participant_id=f"mtp_{uuid4().hex}",
                thread_id=thread.thread_id,
                party_kind="worker",
                party_id=worker_id,
                joined_at=now,
                left_at=None,
            )
        )

    def _worker_intervals(self, thread_id: str, worker_id: str | None) -> list[MessageThreadParticipant]:
        if worker_id is None:
            return []
        return [
            row
            for row in self._threads.list_participants(thread_id)
            if row.party_kind == "worker" and row.party_id == worker_id
        ]

    def _require_read_access(self, thread: MessageThread, actor: ActorContext) -> None:
        if actor.role == ActorRole.OPERATOR:
            self._require_operator_venue(actor, thread.venue_id)
            return
        if actor.role != ActorRole.WORKER:
            raise ForbiddenError("This message thread is not available.")
        if thread.kind in ("direct", "employment") and thread.worker_id == actor.effective_worker_id:
            return
        if thread.kind == "shift_group" and self._worker_intervals(
            thread.thread_id, actor.effective_worker_id
        ):
            return
        raise ForbiddenError("Worker can only access their own message threads.")

    def _require_can_post(self, thread: MessageThread, actor: ActorContext) -> None:
        self._require_read_access(thread, actor)
        if not self._can_post(thread, actor):
            raise ForbiddenError("You are no longer an active participant in this thread.")

    def _can_post(self, thread: MessageThread, actor: ActorContext) -> bool:
        if actor.role == ActorRole.OPERATOR:
            return actor.account_id == thread.venue_id
        if thread.kind == "shift_group":
            return any(
                row.left_at is None
                for row in self._worker_intervals(thread.thread_id, actor.effective_worker_id)
            )
        return thread.worker_id == actor.effective_worker_id

    def _employment_relationships(self, actor: ActorContext) -> list[WorkerRelationship]:
        if actor.role == ActorRole.WORKER:
            worker_id = actor.effective_worker_id
            if worker_id is None:
                return []
            rows = self._relationships.list_for_worker(worker_id)
        elif actor.role == ActorRole.OPERATOR and actor.account_id:
            rows = self._relationships.list_for_venue(actor.account_id, status="active")
        else:
            raise ForbiddenError("Employment threads require a worker or venue account.")
        return [row for row in rows if row.status == "active" and row.relationship_type in EMPLOYED_TYPES]

    def _active_employment(self, relationship_id: str) -> WorkerRelationship:
        relationship = self._relationships.get(relationship_id)
        if (
            relationship is None
            or relationship.status != "active"
            or relationship.relationship_type not in EMPLOYED_TYPES
        ):
            raise NotFoundError("Active employment relationship not found.")
        return relationship

    def _require_relationship_access(
        self, actor: ActorContext, relationship: WorkerRelationship
    ) -> None:
        if actor.role == ActorRole.OPERATOR:
            self._require_operator_venue(actor, relationship.venue_id)
            return
        if actor.role == ActorRole.WORKER and actor.effective_worker_id == relationship.worker_id:
            return
        raise ForbiddenError("This employment thread is not available.")

    def _direct_context(
        self, shift_id: str, application_id: str | None, booking_id: str | None
    ) -> tuple[Application | None, Booking | None, str]:
        application = self._get_application(application_id, shift_id) if application_id else None
        booking = self._get_booking(booking_id, shift_id) if booking_id else None
        if application and booking is None and application.booking_id:
            booking = self._bookings.get(application.booking_id)
        if booking and application is None:
            application = self._applications.find_by_worker_and_shift(booking.worker_id, shift_id)
        if application and booking and application.worker_id != booking.worker_id:
            raise ValidationError("Application and booking belong to different workers.")
        return application, booking, application.worker_id if application else booking.worker_id

    def _enrich_direct(
        self, thread: MessageThread, application: Application | None, booking: Booking | None
    ) -> MessageThread:
        updated = thread.model_copy(
            update={
                "application_id": thread.application_id or (
                    application.application_id if application else None
                ),
                "booking_id": thread.booking_id or (booking.booking_id if booking else None),
            }
        )
        return self._threads.save(updated) if updated != thread else thread

    def _new_thread(
        self,
        kind: str,
        shift: Shift,
        worker_id: str | None = None,
        application_id: str | None = None,
        booking_id: str | None = None,
    ) -> MessageThread:
        venue_id = self._venue_id(shift)
        venue = self._venue(venue_id)
        identity = worker_id if kind == "direct" else shift.shift_id
        return MessageThread(
            thread_id=_thread_id(kind, shift.shift_id, identity),
            kind=kind,
            venue_id=venue_id,
            shift_id=shift.shift_id,
            application_id=application_id,
            booking_id=booking_id,
            relationship_id=None,
            worker_id=worker_id,
            role_snapshot=shift.role,
            venue_name_snapshot=venue.name,
            created_at=utc_now(),
        )

    def _shift(self, shift_id: str) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is None:
            raise NotFoundError(f"Shift not found: {shift_id}")
        return shift

    def _venue(self, venue_id: str) -> Venue:
        venue = self._organisations.get_venue(venue_id)
        if venue is None:
            raise NotFoundError("Venue not found.")
        return venue

    @staticmethod
    def _venue_id(shift: Shift) -> str:
        if not shift.account_id:
            raise ValidationError("Shift is not linked to a venue.")
        return shift.account_id

    @staticmethod
    def _require_operator_venue(actor: ActorContext, venue_id: str) -> None:
        if actor.role != ActorRole.OPERATOR or actor.account_id != venue_id:
            raise ForbiddenError("Operator can only access messages for the active venue.")

    def _require_direct_access(self, actor: ActorContext, shift: Shift, worker_id: str) -> None:
        if actor.role == ActorRole.OPERATOR:
            self._require_operator_venue(actor, self._venue_id(shift))
            return
        if actor.role == ActorRole.WORKER and worker_id == actor.effective_worker_id:
            return
        raise ForbiddenError("Worker can only access their own message threads.")

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

    def _publish_message(self, message: Message, thread: MessageThread, actor: ActorContext) -> None:
        recipients: list[tuple[str, str]] = []
        if thread.kind == "shift_group":
            recipients.append(("venue", thread.venue_id))
            recipients.extend(
                ("worker", row.party_id)
                for row in self._threads.list_participants(thread.thread_id)
                if row.party_kind == "worker"
                and row.left_at is None
                and not (actor.role == ActorRole.WORKER and row.party_id == actor.effective_worker_id)
            )
        elif actor.role == ActorRole.WORKER:
            recipients.append(("venue", thread.venue_id))
        elif thread.worker_id:
            recipients.append(("worker", thread.worker_id))
        for recipient_kind, recipient_id in recipients:
            self._outbox.publish_notification(
                event_type="message.created",
                aggregate_type="message",
                aggregate_id=message.message_id,
                recipient_kind=recipient_kind,
                recipient_id=recipient_id,
                category="messages",
                title="New message",
                body=_preview(message.content),
                action_kind="message_thread",
                action_entity_id=thread.thread_id,
            )


def _thread_id(kind: str, *parts: str) -> str:
    return f"mth_{uuid5(NAMESPACE_URL, ':'.join((kind, *parts))).hex}"


def _party(actor: ActorContext) -> tuple[str, str]:
    if actor.role == ActorRole.WORKER:
        worker_id = actor.effective_worker_id
        if worker_id is None:
            raise ForbiddenError("Worker profile is required for messaging.")
        return "worker", worker_id
    return "user", actor.user_id


def _sender_party(message: Message) -> tuple[str, str]:
    return ("worker" if message.sender_role == "worker" else "user", message.sender_id)


def _preview(content: str) -> str:
    if len(content) <= NOTIFICATION_BODY_LIMIT:
        return content
    return content[: NOTIFICATION_BODY_LIMIT - 1].rstrip() + "…"
