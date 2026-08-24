from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel, RatingModel, ShiftModel, WorkerProfileModel
from apps.api.src.db.tenancy_models import VenueModel
from apps.api.src.models.rating import Rating
from apps.api.src.repositories.rating_repository import (
    DuplicateRatingError,
    PendingRating,
    UnratedBooking,
)
from packages.domain.src.booking_state import BookingState

_COMPLETED_STATES = {
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
}


class SqlAlchemyRatingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, rating: Rating) -> Rating:
        model = self._session.get(RatingModel, rating.rating_id)
        if model is None:
            model = RatingModel(rating_id=rating.rating_id)
            self._session.add(model)
        model.booking_id = rating.booking_id
        model.rated_by_role = rating.rated_by_role
        model.rater_id = rating.rater_id
        model.stars = rating.stars
        model.comment = rating.comment
        model.created_at = rating.created_at
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateRatingError from exc
        return rating

    def get_by_booking_and_role(self, booking_id: str, role: str) -> Rating | None:
        model = (
            self._session.query(RatingModel)
            .filter_by(booking_id=booking_id, rated_by_role=role)
            .first()
        )
        if model is None:
            return None
        return _to_domain(model)

    def avg_operator_rating_for_worker(self, worker_id: str) -> tuple[float | None, int]:
        row = (
            self._session.query(
                func.avg(RatingModel.stars).label("avg"),
                func.count(RatingModel.rating_id).label("total"),
            )
            .join(BookingModel, BookingModel.booking_id == RatingModel.booking_id)
            .filter(BookingModel.worker_id == worker_id)
            .filter(RatingModel.rated_by_role == "operator")
            .one()
        )
        avg = float(row.avg) if row.avg is not None else None
        return avg, row.total

    def avg_worker_rating_for_venue(self, venue_id: str) -> tuple[float | None, int]:
        row = (
            self._session.query(
                func.avg(RatingModel.stars).label("avg"),
                func.count(RatingModel.rating_id).label("total"),
            )
            .join(BookingModel, BookingModel.booking_id == RatingModel.booking_id)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .filter(ShiftModel.venue_id == venue_id)
            .filter(RatingModel.rated_by_role == "worker")
            .one()
        )
        avg = float(row.avg) if row.avg is not None else None
        return avg, row.total

    def unrated_bookings_for_operator(self, worker_id: str, account_id: str) -> list[UnratedBooking]:
        existing_ids = (
            self._session.query(RatingModel.booking_id)
            .filter(RatingModel.rated_by_role == "operator")
            .subquery()
        )
        rows = (
            self._session.query(BookingModel, ShiftModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .filter(BookingModel.worker_id == worker_id)
            .filter(ShiftModel.account_id == account_id)
            .filter(BookingModel.state.in_(_COMPLETED_STATES))
            .filter(BookingModel.booking_id.notin_(existing_ids))
            .all()
        )
        return [
            UnratedBooking(
                booking_id=b.booking_id,
                shift_id=b.shift_id,
                start_time=b.start_time,
                role=s.role,
                location=s.location,
            )
            for b, s in rows
        ]

    def completed_bookings_for_account(self, account_id: str) -> list[UnratedBooking]:
        rows = (
            self._session.query(BookingModel, ShiftModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .filter(ShiftModel.account_id == account_id)
            .filter(BookingModel.state.in_(_COMPLETED_STATES))
            .order_by(BookingModel.start_time.desc())
            .all()
        )
        return [
            UnratedBooking(
                booking_id=b.booking_id,
                shift_id=b.shift_id,
                start_time=b.start_time,
                role=s.role,
                location=s.location,
            )
            for b, s in rows
        ]

    def pending_for_worker(self, worker_id: str, limit: int = 1) -> list[PendingRating]:
        rated_ids = self._rated_booking_ids("worker")
        rows = (
            self._session.query(BookingModel, ShiftModel, VenueModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .outerjoin(VenueModel, VenueModel.venue_id == ShiftModel.venue_id)
            .filter(BookingModel.worker_id == worker_id)
            .filter(BookingModel.state.in_(_COMPLETED_STATES))
            .filter(BookingModel.booking_id.notin_(rated_ids))
            .order_by(BookingModel.end_time.desc())
            .limit(limit)
            .all()
        )
        return [
            PendingRating(
                booking_id=booking.booking_id,
                shift_id=shift.shift_id,
                target_id=shift.venue_id or shift.operator_id,
                target_name=venue.name if venue else shift.location,
                target_avatar_url=venue.avatar_url if venue else None,
                shift_role=shift.role,
                shift_location=shift.location,
                start_time=booking.start_time,
                end_time=booking.end_time,
            )
            for booking, shift, venue in rows
        ]

    def pending_for_account(self, account_id: str, limit: int = 1) -> list[PendingRating]:
        rated_ids = self._rated_booking_ids("operator")
        rows = (
            self._session.query(BookingModel, ShiftModel, WorkerProfileModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .join(WorkerProfileModel, WorkerProfileModel.worker_id == BookingModel.worker_id)
            .filter(ShiftModel.venue_id == account_id)
            .filter(BookingModel.state.in_(_COMPLETED_STATES))
            .filter(BookingModel.booking_id.notin_(rated_ids))
            .order_by(BookingModel.end_time.desc())
            .limit(limit)
            .all()
        )
        return [
            PendingRating(
                booking_id=booking.booking_id,
                shift_id=shift.shift_id,
                target_id=worker.worker_id,
                target_name=worker.display_name,
                target_avatar_url=worker.avatar_url,
                shift_role=shift.role,
                shift_location=shift.location,
                start_time=booking.start_time,
                end_time=booking.end_time,
            )
            for booking, shift, worker in rows
        ]

    def _rated_booking_ids(self, role: str):
        return select(RatingModel.booking_id).where(RatingModel.rated_by_role == role)


def _to_domain(model: RatingModel) -> Rating:
    return Rating(
        rating_id=model.rating_id,
        booking_id=model.booking_id,
        rated_by_role=model.rated_by_role,
        rater_id=model.rater_id,
        stars=model.stars,
        comment=model.comment,
        created_at=model.created_at,
    )
