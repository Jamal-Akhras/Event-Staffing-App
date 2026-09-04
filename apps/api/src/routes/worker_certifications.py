from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import _now_or
from apps.api.src.models.worker_certification import (
    WorkerCertification,
    normalize_certification_name,
)
from apps.api.src.repository_dependencies import get_worker_certification_repo
from apps.api.src.schemas_certifications import CertificationResponse, CertificationUpsertRequest

router = APIRouter(tags=["certifications"])

NAME_PATH = Path(min_length=2, max_length=120)


@router.get("/me/certifications", response_model=list[CertificationResponse])
def list_my_certifications(
    actor: ActorContext = Depends(get_actor_context),
    repo=Depends(get_worker_certification_repo),
) -> list[CertificationResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    return [_view(item) for item in repo.list_for_worker(actor.effective_worker_id)]


@router.put("/me/certifications/{name}", response_model=CertificationResponse)
def upsert_certification(
    payload: CertificationUpsertRequest,
    name: str = NAME_PATH,
    actor: ActorContext = Depends(get_actor_context),
    repo=Depends(get_worker_certification_repo),
) -> CertificationResponse:
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.effective_worker_id
    normalized = normalize_certification_name(name)
    if not normalized:
        raise HTTPException(status_code=400, detail="A certification needs a real name.")
    now = _now_or(payload.now)
    existing = repo.get(worker_id, normalized)
    saved = repo.save(
        WorkerCertification(
            certification_id=existing.certification_id if existing else str(uuid4()),
            worker_id=worker_id,
            name=normalized,
            display_name=payload.display_name.strip(),
            expires_at=payload.expires_at,
            reference=payload.reference,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
    )
    return _view(saved)


@router.delete("/me/certifications/{name}", status_code=204)
def delete_certification(
    name: str = NAME_PATH,
    actor: ActorContext = Depends(get_actor_context),
    repo=Depends(get_worker_certification_repo),
) -> None:
    require_role(actor.role, {ActorRole.WORKER})
    if not repo.delete(actor.effective_worker_id, normalize_certification_name(name)):
        raise HTTPException(status_code=404, detail="That certification was not found.")


def _view(item: WorkerCertification) -> CertificationResponse:
    return CertificationResponse(
        certification_id=item.certification_id,
        name=item.name,
        display_name=item.display_name,
        expires_at=item.expires_at,
        reference=item.reference,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
