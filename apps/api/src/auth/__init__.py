"""Authentication module for JWT-based authentication."""

from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.auth.jwt import create_access_token, decode_access_token, create_reset_token, decode_reset_token
from apps.api.src.auth.dependencies import (
    ActorContext,
    ActorRole,
    get_actor_context,
    get_actor_role,
    get_current_user,
    require_operator_owner,
    require_worker_owner,
    require_role,
    extract_user_id_from_token,
)

__all__ = [
    "ActorRole",
    "ActorContext",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "create_reset_token",
    "decode_reset_token",
    "get_current_user",
    "require_operator_owner",
    "require_worker_owner",
    "get_actor_role",
    "get_actor_context",
    "require_role",
    "extract_user_id_from_token",
]
