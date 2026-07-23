from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationModel, ShiftModel
from apps.api.src.models.application import Application
from apps.api.src.repositories.application_repository import DuplicateApplicationError


class SqlAlchemyApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, application_id: str) -> Application | None:
        model = self._session.get(ApplicationModel, application_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, application: Application) -> Application:
        model = self._session.get(ApplicationModel, application.application_id)
        if model is None:
            model = ApplicationModel(application_id=application.application_id)
            self._session.add(model)
        _apply_domain(model, application)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateApplicationError("Worker has already applied to this shift.") from exc
        return application

    def list_recent(
        self,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        return self._list(limit, status=status, shift_id=shift_id)

    def list_by_worker(
        self,
        worker_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[Application]:
        return self._list(
            limit,
            worker_id=worker_id,
            operator_id=operator_id,
            status=status,
            shift_id=shift_id,
        )

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        return self._list(
            limit,
            worker_id=worker_id,
            operator_id=operator_id,
            status=status,
            shift_id=shift_id,
        )

    def list_for_account(
        self,
        account_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        return self._list(
            limit,
            worker_id=worker_id,
            account_id=account_id,
            status=status,
            shift_id=shift_id,
        )

    def find_by_worker_and_shift(self, worker_id: str, shift_id: str) -> Application | None:
        model = (
            self._session.query(ApplicationModel)
            .filter(
                ApplicationModel.worker_id == worker_id,
                ApplicationModel.shift_id == shift_id
            )
            .first()
        )
        if model is None:
            return None
        return _to_domain(model)

    def _list(
        self,
        limit: int,
        worker_id: str | None = None,
        operator_id: str | None = None,
        account_id: str | None = None,
        status: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        query = self._session.query(ApplicationModel)
        if account_id:
            query = query.join(ShiftModel, ShiftModel.shift_id == ApplicationModel.shift_id)
            query = query.filter(ShiftModel.account_id == account_id)
        if worker_id:
            query = query.filter(ApplicationModel.worker_id == worker_id)
        if operator_id:
            query = query.filter(ApplicationModel.operator_id == operator_id)
        if status:
            query = query.filter(ApplicationModel.status == status)
        if shift_id:
            query = query.filter(ApplicationModel.shift_id == shift_id)
        rows = query.order_by(desc(ApplicationModel.created_at)).limit(limit).all()
        return [_to_domain(row) for row in rows]


def _to_domain(model: ApplicationModel) -> Application:
    return Application(
        application_id=model.application_id,
        shift_id=model.shift_id,
        worker_id=model.worker_id,
        operator_id=model.operator_id,
        start_time=model.start_time,
        end_time=model.end_time,
        message=model.message,
        booking_id=model.booking_id,
        status=model.status,
        created_at=model.created_at,
        decided_at=model.decided_at,
    )


def _apply_domain(model: ApplicationModel, application: Application) -> None:
    model.shift_id = application.shift_id
    model.worker_id = application.worker_id
    model.operator_id = application.operator_id
    model.start_time = application.start_time
    model.end_time = application.end_time
    model.message = application.message
    model.booking_id = application.booking_id
    model.status = application.status
    model.created_at = application.created_at
    model.decided_at = application.decided_at
