from __future__ import annotations

from apps.api.src.auth import ActorContext
from apps.api.src.services.charge_recorder import ChargeRecorder
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.relationship_service import RelationshipService
from packages.domain.src.booking import Booking


def record_approval_effects(
    booking: Booking,
    actor: ActorContext,
    recorder: EventRecorder,
    charges: ChargeRecorder,
    relationships: RelationshipService | None,
) -> None:
    charge = charges.freeze(booking, booking.approved_at)
    recorder.record(
        "billing.charge_frozen",
        "lifecycle",
        actor=actor,
        subject_type="booking_charge",
        subject_id=charge.charge_id,
        worker_id=booking.worker_id,
        context={
            "booking_id": charge.booking_id,
            "hours": str(charge.hours),
            "pay_rate": str(charge.pay_rate),
            "wages": str(charge.wages),
            "fee": str(charge.fee),
            "total": str(charge.total),
            "fee_waived": charge.fee_waived,
        },
    )
    if relationships is None or not charge.account_id:
        return

    first = relationships.record_first_shift(charge.account_id, booking.worker_id, booking.approved_at)
    if first is None:
        return
    recorder.record(
        "relationship.created",
        "lifecycle",
        actor=actor,
        subject_type="worker_relationship",
        subject_id=first.relationship_id,
        worker_id=booking.worker_id,
        context={"venue_id": first.venue_id, "relationship_type": first.relationship_type},
    )
