from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_event_recorder,
    get_idempotency_service,
    get_worker_profile_repo,
)
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.routes.availability_views import exception_view, rule_view
from apps.api.src.routes.idempotency_support import (
    IdempotencyKeyHeader,
    replayed,
    start_or_conflict,
)
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_availability import (
    AvailabilityExceptionCreateRequest,
    AvailabilityExceptionResponse,
    AvailabilityRulesReplaceRequest,
    AvailabilityRulesResponse,
    WorkPreferencesResponse,
    WorkPreferencesUpdateRequest,
)
from apps.api.src.services.availability_management_service import AvailabilityManagementService
from apps.api.src.services.errors import NotFoundError, ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyService
from apps.api.src.service_dependencies_availability import get_availability_management_service

router = APIRouter(tags=["worker availability"])


@router.get("/me/availability/rules", response_model=AvailabilityRulesResponse)
def list_rules(
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
) -> AvailabilityRulesResponse:
    worker_id = _worker_of(actor)
    return AvailabilityRulesResponse(rules=[rule_view(rule) for rule in service.list_rules(worker_id)])


@router.put("/me/availability/rules", response_model=AvailabilityRulesResponse)
def replace_rules(
    payload: AvailabilityRulesReplaceRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> AvailabilityRulesResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "availability.rules.replace",
        idempotency_key,
        payload.model_dump(mode="json"),
    )
    if started.cached_response is not None:
        return replayed(response, AvailabilityRulesResponse, started.cached_response)
    rules = service.replace_rules(
        worker_id, [rule.model_dump() for rule in payload.rules], utc_now()
    )
    recorder.record(
        "availability.rules_replaced",
        "lifecycle",
        actor=actor,
        subject_type="worker_availability",
        subject_id=worker_id,
        context={"rule_count": len(rules)},
    )
    result = AvailabilityRulesResponse(rules=[rule_view(rule) for rule in rules])
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.get("/me/availability/exceptions", response_model=list[AvailabilityExceptionResponse])
def list_exceptions(
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
) -> list[AvailabilityExceptionResponse]:
    worker_id = _worker_of(actor)
    return [exception_view(item) for item in service.list_exceptions(worker_id)]


@router.post(
    "/me/availability/exceptions",
    response_model=AvailabilityExceptionResponse,
    status_code=201,
)
def create_exception(
    payload: AvailabilityExceptionCreateRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> AvailabilityExceptionResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "availability.exception.create",
        idempotency_key,
        payload.model_dump(mode="json"),
    )
    if started.cached_response is not None:
        return replayed(response, AvailabilityExceptionResponse, started.cached_response)
    item = service.create_exception(
        worker_id,
        payload.kind,
        payload.start_time,
        payload.end_time,
        payload.note,
        utc_now(),
    )
    recorder.record(
        "availability.exception_created",
        "lifecycle",
        actor=actor,
        subject_type="availability_exception",
        subject_id=item.exception_id,
        context={"kind": item.kind.value},
    )
    result = exception_view(item)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.delete(
    "/me/availability/exceptions/{exception_id}",
    response_model=AvailabilityExceptionResponse,
)
def delete_exception(
    exception_id: str,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> AvailabilityExceptionResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "availability.exception.delete",
        idempotency_key,
        {"exception_id": exception_id},
    )
    if started.cached_response is not None:
        return replayed(response, AvailabilityExceptionResponse, started.cached_response)
    try:
        item = service.delete_exception(worker_id, exception_id)
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "availability.exception_deleted",
        "lifecycle",
        actor=actor,
        subject_type="availability_exception",
        subject_id=item.exception_id,
        context={"kind": item.kind.value},
    )
    result = exception_view(item)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.put("/me/work-preferences", response_model=WorkPreferencesResponse)
def update_work_preferences(
    payload: WorkPreferencesUpdateRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    profiles: WorkerProfileRepository = Depends(get_worker_profile_repo),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> WorkPreferencesResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "work_preferences.update",
        idempotency_key,
        payload.model_dump(mode="json"),
    )
    if started.cached_response is not None:
        return replayed(response, WorkPreferencesResponse, started.cached_response)
    profile = profiles.get(worker_id)
    if profile is None:
        raise_service_error(NotFoundError("Worker profile not found."))
    profiles.save(
        replace(profile, marketplace_enabled=payload.marketplace_enabled, updated_at=utc_now())
    )
    recorder.record(
        "worker.work_preferences_updated",
        "lifecycle",
        actor=actor,
        subject_type="worker_profile",
        subject_id=worker_id,
        context={"marketplace_enabled": payload.marketplace_enabled},
    )
    result = WorkPreferencesResponse(marketplace_enabled=payload.marketplace_enabled)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


def _worker_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.WORKER})
    return actor.effective_worker_id
