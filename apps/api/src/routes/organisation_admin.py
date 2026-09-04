from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.auth.permissions import MANAGE_MANAGERS, MANAGE_VENUES, require_permission
from apps.api.src.auth.session_tokens import issue_session
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_organisation_service, get_user_repo
from apps.api.src.models.manager_invitation import ManagerInvitation
from apps.api.src.models.organisation import OrganisationMembership
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.auth.password import hash_password
from apps.api.src.models.user import User
from apps.api.src.schemas_organisation_admin import (
    InvitationAcceptRequest,
    InvitedRegisterRequest,
    ManagerInviteRequest,
    MemberResponse,
    MemberRoleUpdateRequest,
    SwitchVenueRequest,
    InvitationResponse,
    VenueCreateRequest,
)
from apps.api.src.schemas_tenancy import VenueSummaryResponse
from apps.api.src.auth.schemas import TokenResponse
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.organisation_service import OrganisationService

router = APIRouter(tags=["organisation admin"])


@router.post("/organisations/me/venues", response_model=VenueSummaryResponse)
def create_venue(
    payload: VenueCreateRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
) -> VenueSummaryResponse:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_VENUES)
    try:
        venue = service.create_venue(
            organisation_id, payload.name, payload.market_id, payload.venue_type,
            payload.default_location, utc_now(),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return VenueSummaryResponse(
        venue_id=venue.venue_id,
        organisation_id=venue.organisation_id,
        name=venue.name,
        country=venue.country,
        currency=venue.currency,
        venue_type=venue.venue_type,
        default_location=venue.default_location,
        market_id=venue.market_id,
    )


@router.get("/organisations/me/members", response_model=list[MemberResponse])
def list_members(
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
) -> list[MemberResponse]:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_MANAGERS)
    return [
        _member_view(membership, email)
        for membership, email in service.list_members(organisation_id)
    ]


@router.post("/organisations/me/members/invite", response_model=InvitationResponse)
def invite_member(
    payload: ManagerInviteRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
) -> InvitationResponse:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_MANAGERS)
    try:
        invitation = service.invite_manager(
            organisation_id,
            payload.email,
            payload.role,
            tuple(payload.venue_ids) if payload.venue_ids else None,
            actor.user_id,
            utc_now(),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return _invitation_view(invitation)


@router.put("/organisations/me/members/{user_id}", response_model=MemberResponse)
def change_member_role(
    user_id: str,
    payload: MemberRoleUpdateRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
    users: UserRepository = Depends(get_user_repo),
) -> MemberResponse:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_MANAGERS)
    try:
        membership = service.change_role(
            organisation_id, user_id, payload.role,
            tuple(payload.venue_ids) if payload.venue_ids else None, utc_now(),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    user = users.get(user_id)
    return _member_view(membership, user.email if user else None)


@router.delete("/organisations/me/members/{user_id}", status_code=204)
def remove_member(
    user_id: str,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
) -> None:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_MANAGERS)
    if user_id == actor.user_id:
        raise HTTPException(status_code=400, detail="Remove yourself by leaving, not here.")
    try:
        service.remove_member(organisation_id, user_id)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/organisations/invitations/accept", response_model=MemberResponse)
def accept_invitation(
    payload: InvitationAcceptRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
    users: UserRepository = Depends(get_user_repo),
) -> MemberResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        membership = service.accept_invitation(payload.token, actor.user_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    user = users.get(actor.user_id)
    return _member_view(membership, user.email if user else None)


@router.post("/auth/switch-venue", response_model=TokenResponse)
def switch_venue(
    payload: SwitchVenueRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: OrganisationService = Depends(get_organisation_service),
    users: UserRepository = Depends(get_user_repo),
) -> TokenResponse:
    organisation_id = _organisation_of(actor)
    try:
        venue = service.venue_for_switch(organisation_id, actor.user_id, payload.venue_id)
    except ServiceError as exc:
        raise_service_error(exc)
    user = users.get(actor.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")
    users.save(replace(user, account_id=venue.venue_id, updated_at=utc_now()))
    return issue_session(
        user,
        organisation_id=organisation_id,
        currency=venue.currency,
        venue_id=venue.venue_id,
    )


@router.post("/auth/register/invited", response_model=TokenResponse)
def register_invited(
    payload: InvitedRegisterRequest,
    service: OrganisationService = Depends(get_organisation_service),
    users: UserRepository = Depends(get_user_repo),
) -> TokenResponse:
    if users.get_by_email(payload.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    now = utc_now()
    user = users.save(
        User(
            user_id=str(uuid4()),
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role="operator",
            account_id=None,
            worker_profile_id=None,
            is_active=True,
            created_at=now,
            updated_at=now,
            email_verified=True,
        )
    )
    try:
        membership = service.accept_invitation(payload.token, user.user_id, now)
    except ServiceError as exc:
        raise_service_error(exc)
    home_venue = service.default_venue_for(membership)
    user = users.save(replace(user, account_id=home_venue.venue_id, updated_at=now))
    return issue_session(
        user,
        organisation_id=membership.organisation_id,
        currency=home_venue.currency,
        venue_id=home_venue.venue_id,
    )


def _organisation_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.organisation_id:
        raise HTTPException(status_code=403, detail="This account has no organisation.")
    return actor.organisation_id


def _member_view(membership: OrganisationMembership, email: str | None) -> MemberResponse:
    return MemberResponse(
        user_id=membership.user_id,
        email=email,
        role=membership.role.value,
        venue_ids=list(membership.venue_scope) if membership.venue_scope else None,
        created_at=membership.created_at,
    )


def _invitation_view(invitation: ManagerInvitation) -> InvitationResponse:
    return InvitationResponse(
        invitation_id=invitation.invitation_id,
        email=invitation.email,
        role=invitation.role,
        venue_ids=list(invitation.venue_scope) if invitation.venue_scope else None,
        token=invitation.token,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
    )
