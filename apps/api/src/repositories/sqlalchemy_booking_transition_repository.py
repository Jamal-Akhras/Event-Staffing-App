from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.booking_transition_models import BookingTransitionModel
from apps.api.src.models.booking_transition import BookingTransition


class SqlAlchemyBookingTransitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, transition: BookingTransition) -> BookingTransition:
        self._session.add(
            BookingTransitionModel(
                **{name: getattr(transition, name) for name in BookingTransition.__dataclass_fields__}
            )
        )
        self._session.flush()
        return transition

    def list_for_booking(self, booking_id: str) -> list[BookingTransition]:
        rows = self._session.execute(
            select(BookingTransitionModel)
            .where(BookingTransitionModel.booking_id == booking_id)
            .order_by(BookingTransitionModel.occurred_at)
        ).scalars().all()
        return [
            BookingTransition(**{name: getattr(row, name) for name in BookingTransition.__dataclass_fields__})
            for row in rows
        ]
