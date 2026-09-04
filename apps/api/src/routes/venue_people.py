from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_event_recorder, get_people_service, get_relationship_service
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.routes.venue_join_codes import relationship_view
from apps.api.src.schemas_workforce import (
    DirectoryEntryResponse,
    EmploymentInviteRequest,
    EndRelationshipRequest,
    TermsUpdateRequest,
    WorkerRelationshipResponse,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.people_service import DirectoryEntry, PeopleService
from apps.api.src.services.relationship_service import RelationshipService

router = APIRouter(tags=["workforce"])

WORKER_PATH = Path(min_length=1, max_length=100)


@router.get("/venues/me/people", response_model=list[DirectoryEntryResponse])
def list_people(
    actor: ActorContext = Depends(get_actor_context),
    service: PeopleService = Depends(get_people_service),
) -> list[DirectoryEntryResponse]:
    return [_entry_view(entry) for entry in service.directory(_venue_of(actor), utc_now())]


@router.post("/venues/me/people/{worker_id}/pool", response_model=WorkerRelationshipResponse)
def add_to_pool(
    worker_id: str = WORKER_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    venue_id = _venue_of(actor)
    try:
        return relationship_view(service.promote_to_pool(venue_id, worker_id, utc_now(), actor.user_id))
    except ServiceError as exc:
        raise_service_error(exc)


@router.delete("/venues/me/people/{worker_id}/pool", response_model=WorkerRelationshipResponse)
def remove_from_pool(
    worker_id: str = WORKER_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    venue_id = _venue_of(actor)
    try:
        return relationship_view(service.remove_from_pool(venue_id, worker_id, utc_now(), actor.user_id))
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/venues/me/people/{worker_id}/invite", response_model=WorkerRelationshipResponse)
def invite_to_employment(
    payload: EmploymentInviteRequest,
    worker_id: str = WORKER_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    venue_id = _venue_of(actor)
    try:
        return relationship_view(
            service.invite_to_employment(
                venue_id,
                worker_id,
                payload.relationship_type,
                utc_now(),
                actor.user_id,
                default_role=payload.default_role,
            )
        )
    except ServiceError as exc:
        raise_service_error(exc)


@router.put("/venues/me/people/{worker_id}/terms", response_model=WorkerRelationshipResponse)
def set_terms(
    payload: TermsUpdateRequest,
    worker_id: str = WORKER_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> WorkerRelationshipResponse:
    venue_id = _venue_of(actor)
    try:
        relationship = service.set_terms(
            venue_id,
            worker_id,
            utc_now(),
            agreed_rate=payload.agreed_rate,
            contracted_hours_per_week=payload.contracted_hours_per_week,
            default_role=payload.default_role,
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "relationship.terms_updated",
        "audit",
        actor=actor,
        subject_type="worker_relationship",
        subject_id=relationship.relationship_id,
        worker_id=worker_id,
        context={
            "agreed_rate": str(relationship.agreed_rate),
            "contracted_hours_per_week": str(relationship.contracted_hours_per_week),
        },
    )
    return relationship_view(relationship)


@router.post("/venues/me/people/{worker_id}/end", response_model=WorkerRelationshipResponse)
def end_relationship(
    payload: EndRelationshipRequest,
    worker_id: str = WORKER_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    venue_id = _venue_of(actor)
    try:
        return relationship_view(
            service.end(venue_id, worker_id, utc_now(), actor.user_id, payload.reason)
        )
    except ServiceError as exc:
        raise_service_error(exc)


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _entry_view(entry: DirectoryEntry) -> DirectoryEntryResponse:
    relationship = entry.relationship
    return DirectoryEntryResponse(
        worker_id=relationship.worker_id,
        display_name=entry.display_name,
        role=entry.role,
        relationship_id=relationship.relationship_id,
        relationship_type=relationship.relationship_type,
        status=relationship.status,
        agreed_rate=relationship.agreed_rate,
        contracted_hours_per_week=relationship.contracted_hours_per_week,
        start_date=relationship.start_date,
        end_date=relationship.end_date,
        reliability_score=entry.reliability_score,
        avatar_url=entry.avatar_url,
        allows_recontact=entry.allows_recontact,
        shifts_with_you=entry.totals.shifts,
        hours_with_you=entry.totals.hours,
        wages_to_date=entry.totals.wages,
        fees_to_date=entry.totals.fees,
        last_worked=entry.totals.last_worked,
        current_status=entry.current_status,
        availability_configured=entry.availability_configured,
    )
