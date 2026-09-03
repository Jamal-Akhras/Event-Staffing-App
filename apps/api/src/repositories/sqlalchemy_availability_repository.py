from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from apps.api.src.db.availability_models import (
    AvailabilityExceptionModel,
    AvailabilityRuleModel,
    TimeOffRequestModel,
)
from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityExceptionKind,
    AvailabilityRule,
    TimeOffRequest,
    TimeOffStatus,
)


class SqlAlchemyAvailabilityRuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, rule: AvailabilityRule) -> AvailabilityRule:
        model = self._session.get(AvailabilityRuleModel, rule.rule_id)
        if model is None:
            model = AvailabilityRuleModel(rule_id=rule.rule_id)
            self._session.add(model)
        _apply_rule(model, rule)
        self._session.flush()
        return rule

    def replace_for_worker(
        self, worker_id: str, rules: list[AvailabilityRule]
    ) -> list[AvailabilityRule]:
        self._session.query(AvailabilityRuleModel).filter_by(worker_id=worker_id).delete(
            synchronize_session=False
        )
        for rule in rules:
            model = AvailabilityRuleModel(rule_id=rule.rule_id)
            _apply_rule(model, rule)
            self._session.add(model)
        self._session.flush()
        return self.list_for_worker(worker_id)

    def list_for_worker(self, worker_id: str) -> list[AvailabilityRule]:
        return self.list_for_workers([worker_id])

    def list_for_workers(self, worker_ids: list[str]) -> list[AvailabilityRule]:
        if not worker_ids:
            return []
        rows = (
            self._session.query(AvailabilityRuleModel)
            .filter(AvailabilityRuleModel.worker_id.in_(worker_ids))
            .order_by(
                AvailabilityRuleModel.worker_id,
                AvailabilityRuleModel.weekday,
                AvailabilityRuleModel.start_minute,
                AvailabilityRuleModel.rule_id,
            )
            .all()
        )
        return [_rule_to_domain(row) for row in rows]


class SqlAlchemyAvailabilityExceptionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, exception: AvailabilityException) -> AvailabilityException:
        model = self._session.get(AvailabilityExceptionModel, exception.exception_id)
        if model is None:
            model = AvailabilityExceptionModel(exception_id=exception.exception_id)
            self._session.add(model)
        _apply_exception(model, exception)
        self._session.flush()
        return exception

    def get(self, exception_id: str) -> AvailabilityException | None:
        model = self._session.get(AvailabilityExceptionModel, exception_id)
        return _exception_to_domain(model) if model else None

    def delete(self, exception_id: str) -> None:
        model = self._session.get(AvailabilityExceptionModel, exception_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def list_for_worker(self, worker_id: str) -> list[AvailabilityException]:
        rows = (
            self._session.query(AvailabilityExceptionModel)
            .filter_by(worker_id=worker_id)
            .order_by(AvailabilityExceptionModel.start_time, AvailabilityExceptionModel.exception_id)
            .all()
        )
        return [_exception_to_domain(row) for row in rows]

    def list_overlapping_workers(
        self, worker_ids: list[str], start_time: datetime, end_time: datetime
    ) -> list[AvailabilityException]:
        if not worker_ids:
            return []
        rows = (
            self._session.query(AvailabilityExceptionModel)
            .filter(AvailabilityExceptionModel.worker_id.in_(worker_ids))
            .filter(AvailabilityExceptionModel.start_time < end_time)
            .filter(AvailabilityExceptionModel.end_time > start_time)
            .order_by(AvailabilityExceptionModel.start_time, AvailabilityExceptionModel.exception_id)
            .all()
        )
        return [_exception_to_domain(row) for row in rows]


class SqlAlchemyTimeOffRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, request: TimeOffRequest) -> TimeOffRequest:
        model = self._session.get(TimeOffRequestModel, request.request_id)
        if model is None:
            model = TimeOffRequestModel(request_id=request.request_id)
            self._session.add(model)
        _apply_time_off(model, request)
        self._session.flush()
        return request

    def get(self, request_id: str, for_update: bool = False) -> TimeOffRequest | None:
        query = self._session.query(TimeOffRequestModel).filter_by(request_id=request_id)
        if for_update:
            query = query.with_for_update()
        model = query.one_or_none()
        return _time_off_to_domain(model) if model else None

    def list_for_worker(self, worker_id: str) -> list[TimeOffRequest]:
        return self._list(worker_id=worker_id)

    def list_for_venue(
        self,
        venue_id: str,
        status: TimeOffStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TimeOffRequest]:
        return self._list(venue_id, status, start_time, end_time)

    def list_overlapping_workers(
        self,
        worker_ids: list[str],
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
        statuses: tuple[TimeOffStatus, ...] | None = None,
    ) -> list[TimeOffRequest]:
        if not worker_ids:
            return []
        query = self._session.query(TimeOffRequestModel).filter(
            TimeOffRequestModel.worker_id.in_(worker_ids),
            TimeOffRequestModel.start_time < end_time,
            TimeOffRequestModel.end_time > start_time,
        )
        if venue_id is not None:
            query = query.filter(TimeOffRequestModel.venue_id == venue_id)
        if statuses is not None:
            query = query.filter(TimeOffRequestModel.status.in_(statuses))
        rows = query.order_by(TimeOffRequestModel.start_time, TimeOffRequestModel.request_id).all()
        return [_time_off_to_domain(row) for row in rows]

    def _list(
        self,
        venue_id: str | None = None,
        status: TimeOffStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        worker_id: str | None = None,
    ) -> list[TimeOffRequest]:
        query = self._session.query(TimeOffRequestModel)
        if venue_id is not None:
            query = query.filter(TimeOffRequestModel.venue_id == venue_id)
        if worker_id is not None:
            query = query.filter(TimeOffRequestModel.worker_id == worker_id)
        if status is not None:
            query = query.filter(TimeOffRequestModel.status == status)
        if start_time is not None:
            query = query.filter(TimeOffRequestModel.end_time > start_time)
        if end_time is not None:
            query = query.filter(TimeOffRequestModel.start_time < end_time)
        rows = query.order_by(TimeOffRequestModel.start_time, TimeOffRequestModel.request_id).all()
        return [_time_off_to_domain(row) for row in rows]


def _rule_to_domain(model: AvailabilityRuleModel) -> AvailabilityRule:
    return AvailabilityRule(
        rule_id=model.rule_id,
        worker_id=model.worker_id,
        timezone=model.timezone,
        weekday=model.weekday,
        start_minute=model.start_minute,
        duration_minutes=model.duration_minutes,
        effective_from=model.effective_from,
        effective_until=model.effective_until,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _apply_rule(model: AvailabilityRuleModel, rule: AvailabilityRule) -> None:
    for field in (
        "worker_id",
        "timezone",
        "weekday",
        "start_minute",
        "duration_minutes",
        "effective_from",
        "effective_until",
        "created_at",
        "updated_at",
    ):
        setattr(model, field, getattr(rule, field))


def _exception_to_domain(model: AvailabilityExceptionModel) -> AvailabilityException:
    return AvailabilityException(
        exception_id=model.exception_id,
        worker_id=model.worker_id,
        kind=AvailabilityExceptionKind(model.kind),
        start_time=model.start_time,
        end_time=model.end_time,
        note=model.note,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _apply_exception(
    model: AvailabilityExceptionModel, exception: AvailabilityException
) -> None:
    for field in ("worker_id", "start_time", "end_time", "note", "created_at", "updated_at"):
        setattr(model, field, getattr(exception, field))
    model.kind = exception.kind.value


def _time_off_to_domain(model: TimeOffRequestModel) -> TimeOffRequest:
    return TimeOffRequest(
        request_id=model.request_id,
        worker_id=model.worker_id,
        venue_id=model.venue_id,
        start_time=model.start_time,
        end_time=model.end_time,
        status=TimeOffStatus(model.status),
        reason=model.reason,
        created_at=model.created_at,
        updated_at=model.updated_at,
        decided_at=model.decided_at,
        decided_by_user_id=model.decided_by_user_id,
    )


def _apply_time_off(model: TimeOffRequestModel, request: TimeOffRequest) -> None:
    for field in (
        "worker_id",
        "venue_id",
        "start_time",
        "end_time",
        "reason",
        "created_at",
        "updated_at",
        "decided_at",
        "decided_by_user_id",
    ):
        setattr(model, field, getattr(request, field))
    model.status = request.status.value
