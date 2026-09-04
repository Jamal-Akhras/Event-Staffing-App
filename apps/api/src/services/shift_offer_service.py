from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.booking_transition import BookingTransition
from apps.api.src.models.shift import Shift
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.booking_allocator import (
    AllocationTargetMissingError,
    BookingAllocator,
    OverlappingBookingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.shift_offer_repository import ShiftOfferRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.certification_gate import CertificationGate
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.outbox_publisher import OutboxPublisher
from packages.domain.src.booking import Booking


class ShiftOfferService:
    def __init__(
        self,
        offers: ShiftOfferRepository,
        shifts: ShiftRepository,
        allocator: BookingAllocator,
        relationships: WorkerRelationshipRepository,
        transitions: BookingTransitionRepository,
        escalations,
        outbox: OutboxPublisher,
        certifications: CertificationGate,
    ) -> None:
        self._offers = offers
        self._shifts = shifts
        self._allocator = allocator
        self._relationships = relationships
        self._transitions = transitions
        self._escalations = escalations
        self._outbox = outbox
        self._certifications = certifications

    def offer(
        self, shift: Shift, worker_id: str, source: str, now: datetime,
        expires_at: datetime | None,
    ) -> ShiftOffer:
        return self._offers.save(
            ShiftOffer(
                offer_id=str(uuid4()),
                shift_id=shift.shift_id,
                venue_id=shift.account_id,
                worker_id=worker_id,
                source=source,
                status="pending",
                offered_at=now,
                expires_at=expires_at,
            )
        )

    def list_for_worker(self, worker_id: str) -> list[ShiftOffer]:
        return self._offers.list_for_worker(worker_id)

    def withdraw_for_shift(self, shift_id: str, now: datetime) -> None:
        pending = self._offers.get_pending_for_shift(shift_id)
        if pending is not None:
            self._offers.save(replace(pending, status="withdrawn", responded_at=now))

    def accept(
        self, offer_id: str, worker_id: str, now: datetime, response_source: str = "manual"
    ) -> Booking:
        offer = self._pending_offer(offer_id, worker_id)
        if offer.expires_at is not None and now >= offer.expires_at:
            self._offers.save(replace(offer, status="expired"))
            raise ValidationError("This offer has expired.")
        shift = self._offer_shift(offer, worker_id, now)
        relationship = self._relationships.get_for_venue_worker(offer.venue_id, worker_id)
        if relationship is None or relationship.status != "active":
            raise ValidationError("You no longer have an active relationship with this venue.")
        self._certifications.ensure_certified(worker_id, shift)
        attendance_mode = (
            "employed" if relationship.relationship_type in EMPLOYED_TYPES else "pin"
        )
        try:
            allocated = self._allocator.allocate(
                shift.shift_id, worker_id, now, str(uuid4()), attendance_mode=attendance_mode
            )
        except ShiftFullError as exc:
            raise ValidationError("This shift has already been filled.") from exc
        except WorkerAlreadyBookedError as exc:
            raise ValidationError("You already hold a booking on this shift.") from exc
        except OverlappingBookingError as exc:
            raise ValidationError(
                f"This shift overlaps a booking you already have on shift {exc.clashing_shift_id}."
            ) from exc
        except AllocationTargetMissingError as exc:
            raise NotFoundError("That shift was not found.") from exc
        self._transitions.append(
            BookingTransition(
                transition_id=str(uuid4()),
                booking_id=allocated.booking.booking_id,
                from_state=None,
                to_state="confirmed",
                occurred_at=now,
                actor_user_id=worker_id,
                actor_role="worker",
                reason_code="offer_accepted",
                context={
                    "offer_id": offer.offer_id,
                    "shift_id": shift.shift_id,
                    "response_source": response_source,
                },
            )
        )
        self._offers.save(
            replace(offer, status="accepted", responded_at=now, response_source=response_source)
        )
        self._notify_venue(
            offer, shift, "offer.accepted", "Your offer was accepted",
            f"{shift.role} on {shift.start_time:%d %b} is covered.",
        )
        return allocated.booking

    def decline(self, offer_id: str, worker_id: str, now: datetime) -> ShiftOffer:
        offer = self._pending_offer(offer_id, worker_id)
        declined = self._offers.save(replace(offer, status="declined", responded_at=now))
        shift = self._shifts.get(offer.shift_id)
        if (
            shift is not None
            and shift.status == "open"
            and shift.origin == "assigned"
            and shift.assigned_worker_id == worker_id
        ):
            self._escalations.restart_ladder(offer.shift_id, now)
        if shift is not None:
            self._notify_venue(
                offer, shift, "offer.declined", "Your offer was declined",
                f"{shift.role} on {shift.start_time:%d %b} needs someone else.",
            )
        return declined

    def _pending_offer(self, offer_id: str, worker_id: str) -> ShiftOffer:
        offer = self._offers.get(offer_id)
        if offer is None or offer.worker_id != worker_id:
            raise NotFoundError("That offer was not found.")
        if offer.status != "pending":
            raise ValidationError("This offer has already been answered.")
        return offer

    def _offer_shift(self, offer: ShiftOffer, worker_id: str, now: datetime) -> Shift:
        shift = self._shifts.get(offer.shift_id)
        if shift is None:
            raise NotFoundError("That shift was not found.")
        stale = (
            shift.status != "open"
            or shift.rota_state != "published"
            or shift.origin != "assigned"
            or shift.assigned_worker_id != worker_id
            or now >= shift.start_time
        )
        if stale:
            raise ValidationError("This offer is no longer open: the shift has moved on.")
        return shift

    def _notify_venue(
        self, offer: ShiftOffer, shift: Shift, event_type: str, title: str, body: str
    ) -> None:
        self._outbox.publish_notification(
            event_type=event_type,
            aggregate_type="shift_offer",
            aggregate_id=offer.offer_id,
            recipient_kind="venue",
            recipient_id=offer.venue_id,
            category="shift_changes",
            title=title,
            body=body,
            action_kind="shift",
            action_entity_id=shift.shift_id,
        )
