from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES, WorkerRelationship
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.repository_dependencies import get_account_repo
from apps.api.src.repository_dependencies_workforce import get_worker_relationship_repo
from apps.api.src.schemas_worker_context import MyRelationshipResponse, WorkerContextResponse

router = APIRouter(tags=["worker context"])


@router.get("/me/relationships", response_model=list[MyRelationshipResponse])
def list_my_relationships(
    actor: ActorContext = Depends(get_actor_context),
    relationships: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    accounts: AccountRepository = Depends(get_account_repo),
) -> list[MyRelationshipResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    return [
        _relationship_view(item, accounts)
        for item in relationships.list_for_worker(actor.effective_worker_id)
    ]


@router.get("/me/work-context", response_model=WorkerContextResponse)
def work_context(
    actor: ActorContext = Depends(get_actor_context),
    relationships: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
) -> WorkerContextResponse:
    require_role(actor.role, {ActorRole.WORKER})
    active = [
        item
        for item in relationships.list_for_worker(actor.effective_worker_id)
        if item.status == "active"
    ]
    employed = any(item.relationship_type in EMPLOYED_TYPES for item in active)
    return WorkerContextResponse(
        home_mode="shifts" if employed else "browse",
        employed=employed,
        active_relationships=len(active),
    )


def _relationship_view(
    relationship: WorkerRelationship, accounts: AccountRepository
) -> MyRelationshipResponse:
    venue = accounts.get(relationship.venue_id)
    return MyRelationshipResponse(
        relationship_id=relationship.relationship_id,
        venue_id=relationship.venue_id,
        venue_name=venue.name if venue else None,
        relationship_type=relationship.relationship_type,
        status=relationship.status,
        default_role=relationship.default_role,
        agreed_rate=relationship.agreed_rate,
        contracted_hours_per_week=relationship.contracted_hours_per_week,
        start_date=relationship.start_date,
        end_date=relationship.end_date,
    )
