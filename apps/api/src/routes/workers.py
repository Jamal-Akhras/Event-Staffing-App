from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role, require_worker_owner
from apps.api.src.deps import (
    get_booking_charge_repo,
    get_booking_repo,
    get_market_repo,
    get_organisation_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.datetime_utils import utc_now
from apps.api.src.helpers import _get_worker_profile, _now_or, _worker_private_view, _worker_public_view
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.money import money
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas import (
    EarningsEntryResponse,
    EarningsSummaryResponse,
    ErrorResponse,
    WorkerProfilePrivateResponse,
    WorkerProfileUpdateRequest,
)
from apps.api.src.services.billing_math import worked_hours
from apps.api.src.services.shift_summary import summarise_shifts
from packages.domain.src.booking_state import BookingState

router = APIRouter(tags=["workers"])
_EARNING_STATES = {BookingState.PAID, BookingState.APPROVED, BookingState.CHECKED_OUT}
_PERIOD_WINDOWS = {
    "week": timedelta(days=7),
    "month": timedelta(days=30),
    "year": timedelta(days=365),
}


@router.get("/workers", response_model=list[WorkerProfilePrivateResponse])
def list_all_workers(
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[WorkerProfilePrivateResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    if actor.account_id:
        profiles = repo.list_for_account(actor.account_id)
    else:
        profiles = repo.list_all()
    return [_worker_public_view(p) for p in profiles]


@router.get("/workers/{worker_id}", response_model=WorkerProfilePrivateResponse, responses={404: {"model": ErrorResponse}})
def get_worker_profile(
    worker_id: str,
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> WorkerProfilePrivateResponse:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    profile = _get_worker_profile(repo, worker_id)
    if actor.role == ActorRole.WORKER:
        if actor.effective_worker_id != worker_id:
            raise HTTPException(status_code=403, detail="Worker can only access their own profile.")
        return _worker_private_view(profile)
    return _worker_public_view(profile)


@router.get("/workers/{worker_id}/earnings", response_model=EarningsSummaryResponse)
def get_worker_earnings(
    worker_id: str,
    period: str = "week",
    repo: BookingRepository = Depends(get_booking_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    charge_repo: BookingChargeRepository = Depends(get_booking_charge_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> EarningsSummaryResponse:
    require_worker_owner(actor, worker_id)
    cutoff = utc_now() - _PERIOD_WINDOWS.get(period, _PERIOD_WINDOWS["week"])
    bookings = [
        booking
        for booking in repo.list_by_worker(worker_id, 500)
        if booking.state in _EARNING_STATES and booking.start_time >= cutoff
    ]
    charges = {charge.booking_id: charge for charge in charge_repo.list_for_worker(worker_id)}
    summaries = summarise_shifts([booking.shift_id for booking in bookings], shift_repo, venues)

    entries = [
        _earnings_entry(booking, charges.get(booking.booking_id), summaries.get(booking.shift_id))
        for booking in bookings
    ]
    entries = [entry for entry in entries if entry is not None]
    entries.sort(key=lambda entry: entry.start_time, reverse=True)

    return EarningsSummaryResponse(
        period=period,
        total_paid=money(sum((e.total for e in entries if e.status == "paid"), Decimal("0"))),
        total_pending=money(sum((e.total for e in entries if e.status == "pending"), Decimal("0"))),
        currency=entries[0].currency if entries else "GBP",
        entries=entries,
    )


def _earnings_entry(booking, charge, summary) -> EarningsEntryResponse | None:
    if charge is None and summary is None:
        return None
    status = "paid" if booking.state == BookingState.PAID else "pending"
    if charge is not None:
        hours, rate, total, currency = charge.hours, charge.pay_rate, charge.wages, charge.currency
        role, location = charge.role, summary.location if summary else ""
    else:
        hours = worked_hours(booking)
        rate = summary.pay_rate
        total = money(hours * rate)
        currency = summary.currency
        role, location = summary.role, summary.location
    return EarningsEntryResponse(
        booking_id=booking.booking_id,
        shift_id=booking.shift_id,
        role=role,
        location=location,
        start_time=booking.start_time,
        end_time=booking.end_time,
        hours=round(float(hours), 2),
        pay_rate=rate,
        total=total,
        status=status,
        currency=currency,
        venue_name=summary.venue_name if summary else None,
        frozen=charge is not None,
    )


@router.put("/workers/{worker_id}", response_model=WorkerProfilePrivateResponse, responses={400: {"model": ErrorResponse}})
def update_worker_profile(
    worker_id: str,
    request: WorkerProfileUpdateRequest,
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> WorkerProfilePrivateResponse:
    require_worker_owner(actor, worker_id)
    now = _now_or(request.now)
    existing = repo.get(worker_id)
    reliability_score = 0.0 if existing is None else existing.reliability_score
    badges = [] if existing is None else existing.badges
    avatar_url = None if existing is None else existing.avatar_url
    market_id = request.market_id if request.market_id is not None else (existing.market_id if existing else None)
    if market_id is not None:
        market = market_repo.get(market_id)
        if market is None or not market.is_active:
            raise HTTPException(status_code=400, detail="Invalid worker market.")
    profile = WorkerProfile(
        worker_id=worker_id,
        display_name=request.display_name,
        role=request.role,
        city=request.city,
        experience_years=request.experience_years,
        reliability_score=reliability_score,
        badges=badges,
        bio=request.bio,
        languages=request.languages,
        email=request.email,
        phone=request.phone,
        address=request.address,
        emergency_contact=request.emergency_contact,
        pay_rate=request.pay_rate,
        notes=request.notes,
        updated_at=now,
        avatar_url=avatar_url,
        allow_venue_recontact=request.allow_venue_recontact,
        market_id=market_id,
    )
    return _worker_private_view(repo.save(profile))
