from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_relationship_service
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repository_dependencies import get_account_repo
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.routes.venue_join_codes import relationship_view
from apps.api.src.schemas_workforce import InvitationResponse, WorkerRelationshipResponse
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.relationship_service import RelationshipService

router = APIRouter(tags=["workforce"])

RELATIONSHIP_PATH = Path(min_length=1, max_length=100)


@router.get("/me/invitations", response_model=list[InvitationResponse])
def list_invitations(
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
    accounts: AccountRepository = Depends(get_account_repo),
) -> list[InvitationResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    invitations = service.list_invitations(actor.effective_worker_id)
    return [
        InvitationResponse(
            relationship_id=item.relationship.relationship_id,
            venue_id=item.relationship.venue_id,
            venue_name=_venue_name(accounts, item.relationship.venue_id),
            relationship_type=item.target_type,
            default_role=item.relationship.default_role,
            invited_at=item.relationship.updated_at,
        )
        for item in invitations
    ]


@router.post("/me/invitations/{relationship_id}/accept", response_model=WorkerRelationshipResponse)
def accept_invitation(
    relationship_id: str = RELATIONSHIP_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    return _respond(service, relationship_id, actor, accepted=True)


@router.post("/me/invitations/{relationship_id}/decline", response_model=WorkerRelationshipResponse)
def decline_invitation(
    relationship_id: str = RELATIONSHIP_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: RelationshipService = Depends(get_relationship_service),
) -> WorkerRelationshipResponse:
    return _respond(service, relationship_id, actor, accepted=False)


def _respond(
    service: RelationshipService, relationship_id: str, actor: ActorContext, accepted: bool
) -> WorkerRelationshipResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        return relationship_view(
            service.respond_to_invitation(relationship_id, actor.effective_worker_id, accepted, utc_now())
        )
    except ServiceError as exc:
        raise_service_error(exc)


def _venue_name(accounts: AccountRepository, venue_id: str) -> str | None:
    venue = accounts.get(venue_id)
    return venue.name if venue else None
