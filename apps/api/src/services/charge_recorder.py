from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.partner_code_repository import PartnerCodeRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.services.billing_math import completed_at, money, worked_hours
from apps.api.src.services.org_affiliation import (
    relationship_type_as_of,
    sibling_employed_venue_as_of,
)
from apps.api.src.services.errors import NotFoundError
from packages.domain.src.booking import Booking


class ChargeRecorder:
    def __init__(
        self,
        charges: BookingChargeRepository,
        shifts: ShiftRepository,
        workers: WorkerProfileRepository,
        partner_codes: PartnerCodeRepository,
        fee_percent: Decimal,
        relationships: WorkerRelationshipRepository,
        relationship_transitions: RelationshipTransitionRepository,
        organisations: OrganisationRepository,
    ) -> None:
        self._charges = charges
        self._shifts = shifts
        self._workers = workers
        self._codes = partner_codes
        self._fee_percent = fee_percent
        self._relationships = relationships
        self._relationship_transitions = relationship_transitions
        self._organisations = organisations

    def freeze(self, booking: Booking, now: datetime) -> BookingCharge:
        existing = self._charges.get_for_booking(booking.booking_id)
        if existing is not None:
            return existing
        shift = self._shifts.get(booking.shift_id)
        if shift is None:
            raise NotFoundError(f"Shift {booking.shift_id} is missing for booking {booking.booking_id}.")
        worker = self._workers.get(booking.worker_id)
        hours = worked_hours(booking)
        pay_rate = money(Decimal(shift.pay_rate))
        wages = money(hours * pay_rate)
        waiver_code = self._active_waiver_code(shift.account_id, now)
        relationship_at_start = self._relationship_as_of(shift.account_id, booking.worker_id, booking.start_time)
        source_venue_id = None
        if relationship_at_start in EMPLOYED_TYPES:
            fee_basis = "venue_employed"
        else:
            source_venue_id = sibling_employed_venue_as_of(
                self._organisations,
                self._relationships,
                self._relationship_transitions,
                shift.account_id,
                booking.worker_id,
                booking.start_time,
            )
            if source_venue_id is not None:
                fee_basis = "organisation_employed"
            elif relationship_at_start == "pool":
                fee_basis = "venue_pool"
            else:
                fee_basis = "outside"
        exempt = fee_basis in ("venue_employed", "organisation_employed")
        fee_percent = Decimal("0.00") if exempt else self._fee_percent
        fee = Decimal("0.00") if (waiver_code or exempt) else money(wages * fee_percent / Decimal(100))
        completed = completed_at(booking)
        return self._charges.record(
            BookingCharge(
                charge_id=str(uuid4()),
                booking_id=booking.booking_id,
                shift_id=shift.shift_id,
                account_id=shift.account_id,
                worker_id=booking.worker_id,
                worker_name=worker.display_name if worker and worker.display_name else "Worker",
                role=shift.role,
                period=completed.strftime("%Y-%m"),
                start_time=booking.start_time,
                end_time=booking.end_time,
                completed_at=completed,
                hours=hours,
                pay_rate=pay_rate,
                wages=wages,
                fee_percent=fee_percent,
                fee=fee,
                total=money(wages + fee),
                currency=shift.currency,
                fee_waived=waiver_code is not None,
                waiver_code=waiver_code,
                recorded_at=now,
                worker_relationship=relationship_at_start,
                fee_basis=fee_basis,
                source_venue_id=source_venue_id,
            )
        )

    def _relationship_as_of(self, venue_id: str, worker_id: str, at) -> str:
        return relationship_type_as_of(
            self._relationships, self._relationship_transitions, venue_id, worker_id, at
        )

    def _active_waiver_code(self, account_id: str, now: datetime) -> str | None:
        redemption = self._codes.get_redemption_for_account(account_id)
        if redemption is None or now > redemption.fee_waived_until:
            return None
        waived = [charge for charge in self._charges.list_for_account(account_id) if charge.fee_waived]
        if len(waived) >= redemption.shift_cap:
            return None
        return redemption.code
