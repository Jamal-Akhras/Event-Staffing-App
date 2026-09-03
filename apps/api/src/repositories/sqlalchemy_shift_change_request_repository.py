from __future__ import annotations

from dataclasses import fields

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.shift_change_models import (
    ShiftChangeRequestModel,
    ShiftChangeTransitionModel,
)
from apps.api.src.models.shift_change_request import ShiftChangeRequest, ShiftChangeTransition
from apps.api.src.repositories.shift_change_request_repository import (
    DuplicatePendingChangeError,
    PENDING_STATUSES,
)

_REQUEST_FIELDS = tuple(field.name for field in fields(ShiftChangeRequest))
_TRANSITION_FIELDS = tuple(field.name for field in fields(ShiftChangeTransition))


class SqlAlchemyShiftChangeRequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, request: ShiftChangeRequest) -> ShiftChangeRequest:
        try:
            with self._session.begin_nested():
                model = self._session.get(ShiftChangeRequestModel, request.request_id)
                if model is None:
                    model = ShiftChangeRequestModel(request_id=request.request_id)
                    self._session.add(model)
                for name in _REQUEST_FIELDS:
                    setattr(model, name, getattr(request, name))
                self._session.flush()
        except IntegrityError as exc:
            raise DuplicatePendingChangeError(
                f"Booking {request.booking_id} already has an open change request."
            ) from exc
        return request

    def get(self, request_id: str) -> ShiftChangeRequest | None:
        model = self._session.get(ShiftChangeRequestModel, request_id)
        return _to_request(model) if model is not None else None

    def get_pending_for_booking(self, booking_id: str) -> ShiftChangeRequest | None:
        model = (
            self._session.query(ShiftChangeRequestModel)
            .filter(ShiftChangeRequestModel.booking_id == booking_id)
            .filter(ShiftChangeRequestModel.status.in_(PENDING_STATUSES))
            .one_or_none()
        )
        return _to_request(model) if model is not None else None

    def list_for_worker(self, worker_id: str) -> list[ShiftChangeRequest]:
        rows = (
            self._session.query(ShiftChangeRequestModel)
            .filter(
                (ShiftChangeRequestModel.worker_id == worker_id)
                | (ShiftChangeRequestModel.replacement_worker_id == worker_id)
            )
            .order_by(desc(ShiftChangeRequestModel.created_at))
            .all()
        )
        return [_to_request(row) for row in rows]

    def list_for_venue(self, venue_id: str, status: str | None = None) -> list[ShiftChangeRequest]:
        query = self._session.query(ShiftChangeRequestModel).filter(
            ShiftChangeRequestModel.venue_id == venue_id
        )
        if status is not None:
            query = query.filter(ShiftChangeRequestModel.status == status)
        rows = query.order_by(ShiftChangeRequestModel.created_at).all()
        return [_to_request(row) for row in rows]

    def list_pending(self) -> list[ShiftChangeRequest]:
        rows = (
            self._session.query(ShiftChangeRequestModel)
            .filter(ShiftChangeRequestModel.status.in_(PENDING_STATUSES))
            .order_by(ShiftChangeRequestModel.created_at)
            .all()
        )
        return [_to_request(row) for row in rows]


class SqlAlchemyShiftChangeTransitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, transition: ShiftChangeTransition) -> ShiftChangeTransition:
        model = ShiftChangeTransitionModel(
            **{name: getattr(transition, name) for name in _TRANSITION_FIELDS}
        )
        self._session.add(model)
        self._session.flush()
        return transition

    def list_for_request(self, request_id: str) -> list[ShiftChangeTransition]:
        rows = (
            self._session.query(ShiftChangeTransitionModel)
            .filter(ShiftChangeTransitionModel.request_id == request_id)
            .order_by(ShiftChangeTransitionModel.occurred_at)
            .all()
        )
        return [_to_transition(row) for row in rows]


def _to_request(model: ShiftChangeRequestModel) -> ShiftChangeRequest:
    return ShiftChangeRequest(**{name: getattr(model, name) for name in _REQUEST_FIELDS})


def _to_transition(model: ShiftChangeTransitionModel) -> ShiftChangeTransition:
    return ShiftChangeTransition(**{name: getattr(model, name) for name in _TRANSITION_FIELDS})
