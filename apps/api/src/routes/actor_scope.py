from __future__ import annotations

from fastapi import HTTPException

from apps.api.src.auth import ActorContext, ActorRole


def list_scope(actor: ActorContext, worker_id: str | None, noun: str) -> tuple[str | None, str | None, str | None]:
    if actor.role == ActorRole.WORKER:
        if worker_id is not None and worker_id != actor.effective_worker_id:
            raise HTTPException(status_code=403, detail=f"Worker can only access their own {noun}.")
        return actor.effective_worker_id, None, None
    if actor.account_id:
        return worker_id, None, actor.account_id
    return worker_id, actor.user_id, None
