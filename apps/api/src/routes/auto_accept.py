from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import _now_or
from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_auto_accept import (
    AutoAcceptAttemptResponse,
    AutoAcceptRuleResponse,
    AutoAcceptRuleUpsertRequest,
)
from apps.api.src.service_dependencies_auto_accept import get_auto_accept_service
from apps.api.src.services.auto_accept_service import AutoAcceptService
from apps.api.src.services.errors import ServiceError

router = APIRouter(tags=["auto accept"])


@router.get("/me/auto-accept-rules", response_model=list[AutoAcceptRuleResponse])
def list_auto_accept_rules(
    actor: ActorContext = Depends(get_actor_context),
    service: AutoAcceptService = Depends(get_auto_accept_service),
) -> list[AutoAcceptRuleResponse]:
    worker_id = _worker_of(actor)
    return [_rule_view(rule) for rule in service.list_rules(worker_id)]


@router.put(
    "/me/auto-accept-rules/{venue_id}", response_model=AutoAcceptRuleResponse
)
def upsert_auto_accept_rule(
    venue_id: str,
    payload: AutoAcceptRuleUpsertRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: AutoAcceptService = Depends(get_auto_accept_service),
) -> AutoAcceptRuleResponse:
    worker_id = _worker_of(actor)
    try:
        rule = service.upsert_rule(
            worker_id,
            venue_id,
            payload.enabled,
            payload.roles,
            payload.minimum_rate,
            payload.minimum_notice_hours,
            _now_or(payload.now),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return _rule_view(rule)


@router.delete("/me/auto-accept-rules/{venue_id}", status_code=204)
def delete_auto_accept_rule(
    venue_id: str,
    response: Response,
    actor: ActorContext = Depends(get_actor_context),
    service: AutoAcceptService = Depends(get_auto_accept_service),
) -> None:
    worker_id = _worker_of(actor)
    try:
        service.delete_rule(worker_id, venue_id)
    except ServiceError as exc:
        raise_service_error(exc)
    response.status_code = 204


@router.get(
    "/me/auto-accept-attempts", response_model=list[AutoAcceptAttemptResponse]
)
def list_auto_accept_attempts(
    limit: int = Query(default=25, ge=1, le=100),
    actor: ActorContext = Depends(get_actor_context),
    service: AutoAcceptService = Depends(get_auto_accept_service),
) -> list[AutoAcceptAttemptResponse]:
    worker_id = _worker_of(actor)
    return [_attempt_view(item) for item in service.list_attempts(worker_id, limit)]


def _worker_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.WORKER})
    return actor.effective_worker_id


def _rule_view(rule: WorkerAutoAcceptRule) -> AutoAcceptRuleResponse:
    return AutoAcceptRuleResponse(
        rule_id=rule.rule_id,
        worker_id=rule.worker_id,
        venue_id=rule.venue_id,
        enabled=rule.enabled,
        roles=rule.roles,
        minimum_rate=rule.minimum_rate,
        minimum_notice_hours=rule.minimum_notice_hours,
        version=rule.version,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _attempt_view(attempt: AutoAcceptAttempt) -> AutoAcceptAttemptResponse:
    return AutoAcceptAttemptResponse(
        attempt_id=attempt.attempt_id,
        offer_id=attempt.offer_id,
        rule_id=attempt.rule_id,
        rule_version=attempt.rule_version,
        rule_snapshot=attempt.rule_snapshot,
        evaluated_at=attempt.evaluated_at,
        outcome=attempt.outcome,
        reason=attempt.reason,
    )
