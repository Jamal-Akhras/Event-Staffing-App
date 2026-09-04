from __future__ import annotations

from fastapi import HTTPException

from apps.api.src.auth.actor import ActorContext, ActorRole

OPERATE = "operate"
MANAGE_SETTINGS = "manage_settings"
MANAGE_BILLING = "manage_billing"
MANAGE_VENUES = "manage_venues"
MANAGE_MANAGERS = "manage_managers"

PERMISSION_MATRIX: dict[str, frozenset[str]] = {
    "owner": frozenset(
        {OPERATE, MANAGE_SETTINGS, MANAGE_BILLING, MANAGE_VENUES, MANAGE_MANAGERS}
    ),
    "admin": frozenset({OPERATE, MANAGE_SETTINGS, MANAGE_BILLING, MANAGE_VENUES}),
    "manager": frozenset({OPERATE}),
}


def permissions_of(membership_role: str | None) -> frozenset[str]:
    if membership_role is None:
        return PERMISSION_MATRIX["owner"]
    granted = PERMISSION_MATRIX.get(membership_role)
    if granted is None:
        raise HTTPException(status_code=403, detail=f"Unknown membership role: {membership_role}")
    return granted


def require_permission(actor: ActorContext, permission: str) -> None:
    if actor.role != ActorRole.OPERATOR:
        raise HTTPException(status_code=403, detail="Operator access required.")
    if permission not in permissions_of(actor.membership_role):
        raise HTTPException(
            status_code=403,
            detail=f"Your role does not allow this action ({permission}).",
        )
