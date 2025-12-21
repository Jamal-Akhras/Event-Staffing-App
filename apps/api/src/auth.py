from __future__ import annotations

from enum import Enum

from fastapi import Header, HTTPException


class ActorRole(str, Enum):
    OPERATOR = "operator"
    WORKER = "worker"
    SYSTEM = "system"


def get_actor_role(x_actor_role: str | None = Header(default=None, alias="X-Actor-Role")) -> ActorRole:
    if x_actor_role is None:
        raise HTTPException(status_code=401, detail="Missing X-Actor-Role header.")
    try:
        return ActorRole(x_actor_role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-Actor-Role value.") from exc


def require_role(actor: ActorRole, allowed: set[ActorRole]) -> None:
    if actor not in allowed:
        raise HTTPException(status_code=403, detail="Action not permitted for this role.")
