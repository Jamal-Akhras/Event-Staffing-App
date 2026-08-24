from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.src.datetime_utils import utc_now
from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role, require_verified_actor
from apps.api.src.deps import get_booking_repo, get_organisation_repo, get_rating_repo, get_shift_repo
from apps.api.src.models.rating import Rating
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.rating_repository import DuplicateRatingError, RatingRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas_ratings import (
    CompletedShiftResponse,
    PendingRatingResponse,
    RatingCreateRequest,
    UnratedBookingResponse,
    WorkerRatingSummaryResponse,
    VenueRatingSummaryResponse,
)

router = APIRouter(tags=["ratings"])
_RATEABLE_STATES = {"checked_out", "approved", "paid"}


@router.post("/bookings/{booking_id}/rate", status_code=201)
@limiter.limit("20/hour", key_func=actor_or_ip)
def rate_booking(
    booking_id: str,
    request: Request,
    payload: RatingCreateRequest,
    repo: RatingRepository = Depends(get_rating_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, str]:
    require_verified_actor(actor, "rating completed shifts")
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    booking = booking_repo.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.state.value not in _RATEABLE_STATES:
        raise HTTPException(status_code=409, detail="Ratings open after the shift is completed.")
    shift = shift_repo.get(booking.shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found.")

    role_str = actor.role.value
    rater_id = _require_rating_access(
        actor,
        booking.worker_id,
        booking.operator_id,
        shift.account_id,
    )

    existing = repo.get_by_booking_and_role(booking_id, role_str)
    if existing is not None:
        raise HTTPException(status_code=409, detail="You have already rated this booking.")

    rating = Rating(
        rating_id=str(uuid4()),
        booking_id=booking_id,
        rated_by_role=role_str,
        rater_id=rater_id,
        stars=payload.stars,
        comment=payload.comment,
        created_at=utc_now(),
    )
    try:
        repo.save(rating)
    except DuplicateRatingError:
        raise HTTPException(status_code=409, detail="You have already rated this booking.")
    return {"rating_id": rating.rating_id}


@router.get("/ratings/pending", response_model=list[PendingRatingResponse])
def list_pending_ratings(
    limit: int = Query(default=1, ge=1, le=20),
    repo: RatingRepository = Depends(get_rating_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[PendingRatingResponse]:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    if actor.role == ActorRole.WORKER:
        worker_id = actor.worker_profile_id or actor.user_id
        items = repo.pending_for_worker(worker_id, limit)
    elif actor.account_id:
        items = repo.pending_for_account(actor.account_id, limit)
    else:
        items = []
    return [PendingRatingResponse(**item.__dict__) for item in items]


@router.get("/workers/{worker_id}/rating-summary", response_model=WorkerRatingSummaryResponse)
def get_worker_rating_summary(
    worker_id: str,
    repo: RatingRepository = Depends(get_rating_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> WorkerRatingSummaryResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    avg, total = repo.avg_operator_rating_for_worker(worker_id)
    if actor.account_id:
        unrated = repo.unrated_bookings_for_operator(worker_id, actor.account_id)
    else:
        unrated = []
    return WorkerRatingSummaryResponse(
        avg_stars=round(avg, 1) if avg is not None else None,
        total_ratings=total,
        unrated_bookings=[
            UnratedBookingResponse(
                booking_id=u.booking_id,
                shift_id=u.shift_id,
                start_time=u.start_time,
                role=u.role,
                location=u.location,
            )
            for u in unrated
        ],
    )


@router.get("/venues/{venue_id}/rating-summary", response_model=VenueRatingSummaryResponse)
def get_venue_rating_summary(
    venue_id: str,
    repo: RatingRepository = Depends(get_rating_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> VenueRatingSummaryResponse:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    if organisation_repo.get_venue(venue_id) is None:
        raise HTTPException(status_code=404, detail="Venue not found.")
    avg, total = repo.avg_worker_rating_for_venue(venue_id)
    return VenueRatingSummaryResponse(
        venue_id=venue_id,
        avg_stars=round(avg, 1) if avg is not None else None,
        total_ratings=total,
    )


@router.get("/accounts/me/completed-shifts", response_model=list[CompletedShiftResponse])
def list_completed_shifts(
    repo: RatingRepository = Depends(get_rating_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[CompletedShiftResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        return []
    bookings = repo.completed_bookings_for_account(actor.account_id)
    results = []
    for b in bookings:
        existing = repo.get_by_booking_and_role(b.booking_id, "operator")
        results.append(CompletedShiftResponse(
            booking_id=b.booking_id,
            shift_id=b.shift_id,
            worker_id=_get_worker_id(booking_repo, b.booking_id),
            start_time=b.start_time,
            role=b.role,
            location=b.location,
            operator_rating=existing.stars if existing else None,
        ))
    return results


def _get_worker_id(repo: BookingRepository, booking_id: str) -> str:
    booking = repo.get(booking_id)
    return booking.worker_id if booking else ""


def _require_rating_access(
    actor: ActorContext,
    worker_id: str,
    operator_id: str,
    account_id: str | None,
) -> str:
    if actor.role == ActorRole.WORKER:
        effective_worker_id = actor.worker_profile_id or actor.user_id
        if effective_worker_id != worker_id:
            raise HTTPException(status_code=403, detail="Worker can only rate their own shifts.")
        return effective_worker_id
    if actor.account_id:
        if account_id != actor.account_id:
            raise HTTPException(status_code=403, detail="Operator can only rate shifts at their venue.")
        return actor.user_id
    if operator_id != actor.user_id:
        raise HTTPException(status_code=403, detail="Operator can only rate their own shifts.")
    return actor.user_id
