"""FastAPI dependencies for authentication."""

from dataclasses import dataclass
from enum import Enum

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from apps.api.src.auth.jwt import decode_access_token
from apps.api.src.config import get_bool_env
from apps.api.src.models.user import User
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.deps import get_organisation_repo, get_user_repo

security = HTTPBearer(auto_error=False)

DEV_MODE = get_bool_env("DEV_MODE", False)


class ActorRole(str, Enum):
    """Enumeration of actor roles in the system."""

    WORKER = "worker"
    OPERATOR = "operator"
    SYSTEM = "system"


@dataclass(frozen=True)
class ActorContext:
    user_id: str
    role: ActorRole
    account_id: str | None = None
    worker_profile_id: str | None = None
    organisation_id: str | None = None
    email_verified: bool = False

    @property
    def venue_id(self) -> str | None:
        return self.account_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Dependency that validates JWT and returns the current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header
        user_repo: User repository for database access

    Returns:
        User object if authentication is successful

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    _require_current_session(payload, user)

    return user


async def get_actor_role(
    x_actor_role: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ActorRole:
    """Dependency that returns the role of the current authenticated user.

    In DEV_MODE: uses X-Actor-Role header (no authentication required)
    In production: validates JWT token and extracts role from authenticated user

    Args:
        x_actor_role: Role from X-Actor-Role header (dev mode only)
        credentials: HTTP Bearer credentials from Authorization header
        user_repo: User repository for database access

    Returns:
        ActorRole enum value

    Raises:
        HTTPException: 401 if authentication fails, 403 if role is invalid
    """
    # Dev mode: use X-Actor-Role header
    if DEV_MODE and x_actor_role:
        try:
            return ActorRole(x_actor_role)
        except ValueError:
            raise HTTPException(status_code=403, detail=f"Invalid role: {x_actor_role}")

    # Production mode: require JWT authentication
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    _require_current_session(payload, user)

    try:
        return ActorRole(user.role)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Invalid role: {user.role}")


async def get_actor_context(
    x_actor_role: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
    x_account_id: str | None = Header(default=None),
    x_organisation_id: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
) -> ActorContext:
    if DEV_MODE and x_actor_role:
        try:
            role = ActorRole(x_actor_role)
        except ValueError:
            raise HTTPException(status_code=403, detail=f"Invalid role: {x_actor_role}")
        if not x_actor_id:
            raise HTTPException(status_code=401, detail="X-Actor-Id header is required.")
        account_id = x_account_id or (x_actor_id if role == ActorRole.OPERATOR else None)
        worker_profile_id = x_actor_id if role == ActorRole.WORKER else None
        return ActorContext(
            user_id=x_actor_id,
            role=role,
            account_id=account_id,
            worker_profile_id=worker_profile_id,
            organisation_id=x_organisation_id,
            email_verified=True,
        )

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    _require_current_session(payload, user)

    try:
        role = ActorRole(user.role)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Invalid role: {user.role}")
    organisation_id = None
    if role == ActorRole.OPERATOR:
        if not user.account_id:
            raise HTTPException(status_code=403, detail="Operator has no active venue.")
        venue = organisation_repo.get_venue(user.account_id)
        if venue is None:
            raise HTTPException(status_code=403, detail="Operator venue is unavailable.")
        membership = organisation_repo.get_membership(venue.organisation_id, user.user_id)
        if membership is None:
            raise HTTPException(status_code=403, detail="Operator is not a member of this organisation.")
        organisation_id = venue.organisation_id
    return ActorContext(
        user_id=user.user_id,
        role=role,
        account_id=user.account_id,
        worker_profile_id=user.worker_profile_id,
        organisation_id=organisation_id,
        email_verified=user.email_verified,
    )


def _require_current_session(payload: dict, user: User) -> None:
    token_version = payload.get("session_version", 0)
    if not isinstance(token_version, int) or token_version != user.session_version:
        raise HTTPException(status_code=401, detail="Session has been revoked")


def require_verified_actor(actor: ActorContext, action: str) -> None:
    if get_bool_env("DEV_MODE", False):
        return
    if not actor.email_verified:
        raise HTTPException(
            status_code=403,
            detail=f"Verify your email before {action}.",
        )


def require_role(actor: ActorRole, allowed_roles: set[ActorRole]) -> None:
    """Validate that the actor has one of the allowed roles.

    Args:
        actor: The current actor's role
        allowed_roles: Set of roles that are permitted

    Raises:
        HTTPException: 403 if actor's role is not in allowed_roles
    """
    if actor not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Access forbidden. Required roles: {[r.value for r in allowed_roles]}",
        )


def require_worker_owner(actor: ActorContext, worker_id: str) -> None:
    require_role(actor.role, {ActorRole.WORKER})
    effective_id = actor.worker_profile_id or actor.user_id
    if effective_id != worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own data.")


def require_operator_owner(actor: ActorContext, operator_id: str) -> None:
    require_role(actor.role, {ActorRole.OPERATOR})
    if actor.user_id != operator_id:
        raise HTTPException(status_code=403, detail="Operator can only access their own venue data.")


def extract_user_id_from_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """Extract user_id from a Bearer token without raising on failure.

    Returns the user_id string if the token is valid, or None if absent/invalid.
    Used by endpoints that want to use real identity when available but fall back
    to a default in DEV_MODE when no token is present.
    """
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return payload.get("user_id")
    except Exception:
        return None
