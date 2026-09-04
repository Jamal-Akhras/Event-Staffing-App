from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from apps.api.src.auth.actor import ActorContext, ActorRole
from apps.api.src.auth.jwt import decode_access_token
from apps.api.src.config import get_bool_env
from apps.api.src.models.user import User
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.models.organisation import membership_covers
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.deps import get_organisation_repo, get_user_repo

security = HTTPBearer(auto_error=False)

DEV_MODE = get_bool_env("DEV_MODE", False)

__all__ = ["ActorContext", "ActorRole"]


def _authenticated_session(
    credentials: HTTPAuthorizationCredentials | None, user_repo: UserRepository
) -> tuple[User, dict]:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = user_repo.get(payload.get("user_id") or "")
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if payload.get("session_version", 0) != user.session_version:
        raise HTTPException(status_code=401, detail="Session has been revoked")
    return user, payload


def _authenticated_user(credentials: HTTPAuthorizationCredentials | None, user_repo: UserRepository) -> User:
    return _authenticated_session(credentials, user_repo)[0]


def _role_of(value: str) -> ActorRole:
    try:
        return ActorRole(value)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Invalid role: {value}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    return _authenticated_user(credentials, user_repo)


async def get_actor_context(
    request: Request,
    x_actor_role: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
    x_account_id: str | None = Header(default=None),
    x_organisation_id: str | None = Header(default=None),
    x_membership_role: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
) -> ActorContext:
    if DEV_MODE and x_actor_role:
        role = _role_of(x_actor_role)
        if not x_actor_id:
            raise HTTPException(status_code=401, detail="X-Actor-Id header is required.")
        return _remember(request, ActorContext(
            user_id=x_actor_id,
            role=role,
            account_id=x_account_id or (x_actor_id if role == ActorRole.OPERATOR else None),
            worker_profile_id=x_actor_id if role == ActorRole.WORKER else None,
            organisation_id=x_organisation_id,
            email_verified=True,
            membership_role=(x_membership_role or "owner") if role == ActorRole.OPERATOR else None,
        ))

    user, payload = _authenticated_session(credentials, user_repo)
    role = _role_of(user.role)
    organisation_id = None
    membership_role = None
    venue_scope = None
    active_venue_id = user.account_id
    if role == ActorRole.OPERATOR:
        claimed_venue_id = payload.get("venue_id") or user.account_id
        if not claimed_venue_id:
            raise HTTPException(status_code=403, detail="Operator has no active venue.")
        venue = organisation_repo.get_venue(claimed_venue_id)
        if venue is None:
            raise HTTPException(status_code=403, detail="Operator venue is unavailable.")
        membership = organisation_repo.get_membership(venue.organisation_id, user.user_id)
        if membership is None:
            raise HTTPException(status_code=403, detail="Operator is not a member of this organisation.")
        if not membership_covers(membership, claimed_venue_id):
            raise HTTPException(status_code=403, detail="Your role does not cover this venue.")
        organisation_id = venue.organisation_id
        membership_role = membership.role.value
        venue_scope = membership.venue_scope
        active_venue_id = claimed_venue_id
    return _remember(request, ActorContext(
        user_id=user.user_id,
        role=role,
        account_id=active_venue_id,
        worker_profile_id=user.worker_profile_id,
        organisation_id=organisation_id,
        email_verified=user.email_verified,
        membership_role=membership_role,
        venue_scope=venue_scope,
    ))


def _remember(request: Request, actor: ActorContext) -> ActorContext:
    request.state.actor = actor
    return actor


def require_verified_actor(actor: ActorContext, action: str) -> None:
    if get_bool_env("DEV_MODE", False):
        return
    if not actor.email_verified:
        raise HTTPException(status_code=403, detail=f"Verify your email before {action}.")


def require_role(actor: ActorRole, allowed_roles: set[ActorRole]) -> None:
    if actor not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Access forbidden. Required roles: {[r.value for r in allowed_roles]}",
        )


def require_worker_owner(actor: ActorContext, worker_id: str) -> None:
    require_role(actor.role, {ActorRole.WORKER})
    if actor.effective_worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own data.")


def require_operator_owner(actor: ActorContext, operator_id: str) -> None:
    require_role(actor.role, {ActorRole.OPERATOR})
    if actor.user_id != operator_id:
        raise HTTPException(status_code=403, detail="Operator can only access their own venue data.")
