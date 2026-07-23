from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_booking_repo, get_rating_repo
from apps.api.src.models.rating import Rating
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.rating_repository import RatingRepository
from apps.api.src.schemas_ratings import (
    CompletedShiftResponse,
    RatingCreateRequest,
    UnratedBookingResponse,
    WorkerRatingSummaryResponse,
)

router = APIRouter(tags=["ratings"])


@router.post("/bookings/{booking_id}/rate", status_code=201)
def rate_booking(
    booking_id: str,
    request: RatingCreateRequest,
    repo: RatingRepository = Depends(get_rating_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, str]:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    booking = booking_repo.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found.")

    role_str = actor.role.value

    existing = repo.get_by_booking_and_role(booking_id, role_str)
    if existing is not None:
        raise HTTPException(status_code=409, detail="You have already rated this booking.")

    rating = Rating(
        rating_id=str(uuid4()),
        booking_id=booking_id,
        rated_by_role=role_str,
        stars=request.stars,
        comment=request.comment,
        created_at=datetime.utcnow(),
    )
    repo.save(rating)
    return {"rating_id": rating.rating_id}


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
