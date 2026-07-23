from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_account_repo, get_worker_profile_repo
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas_uploads import UploadResponse
from apps.api.src.services.upload_validation import read_capped_image, validate_extension

router = APIRouter(tags=["uploads"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_file(data: bytes, filename: str) -> str:
    dest = _UPLOAD_DIR / filename
    dest.write_bytes(data)
    return f"/uploads/{filename}"


@router.post("/uploads/avatar", response_model=UploadResponse)
async def upload_worker_avatar(
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
) -> UploadResponse:
    require_role(actor.role, {ActorRole.WORKER})
    ext = validate_extension(file.filename)
    data = await read_capped_image(file)

    worker_id = actor.worker_profile_id or actor.user_id
    filename = f"avatar_{worker_id}{ext}"
    url = _save_file(data, filename)

    existing = repo.get(worker_id)
    if existing is not None:
        updated = replace(existing, avatar_url=url)
        repo.save(updated)

    return UploadResponse(url=url, filename=filename)


@router.post("/uploads/venue-photo", response_model=UploadResponse)
async def upload_venue_photo(
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
) -> UploadResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(400, "No account associated with this operator.")

    ext = validate_extension(file.filename)
    data = await read_capped_image(file)

    filename = f"venue_{actor.account_id}_{uuid4().hex[:8]}{ext}"
    url = _save_file(data, filename)

    account = account_repo.get(actor.account_id)
    if account is not None:
        updated = replace(account, photos=[*account.photos, url])
        account_repo.save(updated)

    return UploadResponse(url=url, filename=filename)


@router.post("/uploads/venue-avatar", response_model=UploadResponse)
async def upload_venue_avatar(
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
) -> UploadResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(400, "No account associated with this operator.")

    ext = validate_extension(file.filename)
    data = await read_capped_image(file)

    filename = f"avatar_venue_{actor.account_id}{ext}"
    url = _save_file(data, filename)

    account = account_repo.get(actor.account_id)
    if account is not None:
        updated = replace(account, avatar_url=url)
        account_repo.save(updated)

    return UploadResponse(url=url, filename=filename)
