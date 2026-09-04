from __future__ import annotations

from dataclasses import fields

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.auto_accept_models import (
    AutoAcceptAttemptModel,
    WorkerAutoAcceptRuleModel,
)
from apps.api.src.db.shift_offer_models import ShiftOfferModel
from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule
from apps.api.src.repositories.auto_accept_repository import (
    DuplicateAutoAcceptAttemptError,
)

_RULE_FIELDS = tuple(field.name for field in fields(WorkerAutoAcceptRule))
_ATTEMPT_FIELDS = tuple(field.name for field in fields(AutoAcceptAttempt))


class SqlAlchemyWorkerAutoAcceptRuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, rule: WorkerAutoAcceptRule) -> WorkerAutoAcceptRule:
        with self._session.begin_nested():
            model = self._model(rule.worker_id, rule.venue_id)
            if model is None:
                model = WorkerAutoAcceptRuleModel(rule_id=rule.rule_id)
                self._session.add(model)
            for name in _RULE_FIELDS:
                setattr(model, name, getattr(rule, name))
            self._session.flush()
        return rule

    def get(self, worker_id: str, venue_id: str) -> WorkerAutoAcceptRule | None:
        model = self._model(worker_id, venue_id)
        return _to_rule(model) if model is not None else None

    def list_for_worker(self, worker_id: str) -> list[WorkerAutoAcceptRule]:
        rows = (
            self._session.query(WorkerAutoAcceptRuleModel)
            .filter(WorkerAutoAcceptRuleModel.worker_id == worker_id)
            .order_by(WorkerAutoAcceptRuleModel.created_at)
            .all()
        )
        return [_to_rule(row) for row in rows]

    def delete(self, worker_id: str, venue_id: str) -> bool:
        model = self._model(worker_id, venue_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def _model(
        self, worker_id: str, venue_id: str
    ) -> WorkerAutoAcceptRuleModel | None:
        return (
            self._session.query(WorkerAutoAcceptRuleModel)
            .filter(WorkerAutoAcceptRuleModel.worker_id == worker_id)
            .filter(WorkerAutoAcceptRuleModel.venue_id == venue_id)
            .one_or_none()
        )


class SqlAlchemyAutoAcceptAttemptRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, attempt: AutoAcceptAttempt) -> AutoAcceptAttempt:
        try:
            with self._session.begin_nested():
                self._session.add(
                    AutoAcceptAttemptModel(
                        **{name: getattr(attempt, name) for name in _ATTEMPT_FIELDS}
                    )
                )
                self._session.flush()
        except IntegrityError as exc:
            if _is_attempt_version_duplicate(exc):
                raise DuplicateAutoAcceptAttemptError(
                    f"Offer {attempt.offer_id} was already evaluated at rule version "
                    f"{attempt.rule_version}."
                ) from exc
            raise
        return attempt

    def get_for_offer_version(
        self, offer_id: str, rule_version: int
    ) -> AutoAcceptAttempt | None:
        model = (
            self._session.query(AutoAcceptAttemptModel)
            .filter(AutoAcceptAttemptModel.offer_id == offer_id)
            .filter(AutoAcceptAttemptModel.rule_version == rule_version)
            .one_or_none()
        )
        return _to_attempt(model) if model is not None else None

    def list_for_worker(self, worker_id: str, limit: int) -> list[AutoAcceptAttempt]:
        rows = (
            self._session.query(AutoAcceptAttemptModel)
            .join(ShiftOfferModel, ShiftOfferModel.offer_id == AutoAcceptAttemptModel.offer_id)
            .filter(ShiftOfferModel.worker_id == worker_id)
            .order_by(desc(AutoAcceptAttemptModel.evaluated_at))
            .limit(limit)
            .all()
        )
        return [_to_attempt(row) for row in rows]


def _to_rule(model: WorkerAutoAcceptRuleModel) -> WorkerAutoAcceptRule:
    return WorkerAutoAcceptRule(**{name: getattr(model, name) for name in _RULE_FIELDS})


def _to_attempt(model: AutoAcceptAttemptModel) -> AutoAcceptAttempt:
    return AutoAcceptAttempt(**{name: getattr(model, name) for name in _ATTEMPT_FIELDS})


def _is_attempt_version_duplicate(exc: IntegrityError) -> bool:
    diagnostic = getattr(exc.orig, "diag", None)
    if (
        diagnostic is not None
        and diagnostic.constraint_name == "uq_auto_accept_attempts_offer_rule_version"
    ):
        return True
    message = str(exc.orig)
    return (
        "UNIQUE constraint failed: auto_accept_attempts.offer_id, "
        "auto_accept_attempts.rule_version"
    ) in message
