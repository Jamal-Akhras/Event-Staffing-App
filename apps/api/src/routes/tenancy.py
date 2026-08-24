from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_organisation_repo
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.schemas_tenancy import OrganisationResponse, VenueSummaryResponse

router = APIRouter(tags=["organisations", "venues"])


@router.get("/organisations/me", response_model=OrganisationResponse)
def get_my_organisation(
    actor: ActorContext = Depends(get_actor_context),
    repo: OrganisationRepository = Depends(get_organisation_repo),
) -> OrganisationResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.organisation_id:
        raise HTTPException(status_code=404, detail="No organisation associated with this user.")
    organisation = repo.get_organisation(actor.organisation_id)
    membership = repo.get_membership(actor.organisation_id, actor.user_id)
    if organisation is None or membership is None:
        raise HTTPException(status_code=404, detail="Organisation membership not found.")
    return OrganisationResponse(
        organisation_id=organisation.organisation_id,
        name=organisation.name,
        country=organisation.country,
        currency=organisation.currency,
        membership_role=membership.role.value,
        created_at=organisation.created_at,
    )


@router.get("/venues", response_model=list[VenueSummaryResponse])
def list_my_venues(
    actor: ActorContext = Depends(get_actor_context),
    repo: OrganisationRepository = Depends(get_organisation_repo),
) -> list[VenueSummaryResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    return [
        VenueSummaryResponse(
            venue_id=venue.venue_id,
            organisation_id=venue.organisation_id,
            name=venue.name,
            country=venue.country,
            currency=venue.currency,
            venue_type=venue.venue_type,
            default_location=venue.default_location,
            market_id=venue.market_id,
        )
        for venue in repo.list_venues_for_user(actor.user_id)
    ]
