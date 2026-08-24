from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role, require_verified_actor
from apps.api.src.deps import get_account_repo, get_worker_profile_repo
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repository_dependencies import get_request_unit_of_work
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas_uploads import UploadResponse
from apps.api.src.services.stored_upload import (
    avatar_key,
    avatar_prefix,
    store_image,
    venue_photo_key,
)
from apps.api.src.services.upload_validation import read_processed_image
from apps.api.src.storage.object_storage import ObjectStorage
from apps.api.src.storage_dependencies import get_object_storage
from apps.api.src.unit_of_work import RequestUnitOfWork

router = APIRouter(tags=["uploads"])


@router.post("/uploads/avatar", response_model=UploadResponse)
@limiter.limit("10/hour", key_func=actor_or_ip)
async def upload_worker_avatar(
    request: Request,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    storage: ObjectStorage = Depends(get_object_storage),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> UploadResponse:
    require_verified_actor(actor, "uploading images")
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.worker_profile_id or actor.user_id
    existing = repo.get(worker_id)
    if existing is None:
        raise HTTPException(404, "Worker profile not found.")

    image = await read_processed_image(file)
    stored = await store_image(
        storage,
        unit_of_work,
        avatar_key("workers", worker_id, image.extension),
        image.data,
        image.content_type,
        existing.avatar_url,
        avatar_prefix("workers", worker_id),
    )
    repo.save(replace(existing, avatar_url=stored.url))

    return UploadResponse(url=stored.url, filename=stored.key.rsplit("/", 1)[-1])


@router.post("/uploads/venue-photo", response_model=UploadResponse)
@limiter.limit("20/hour", key_func=actor_or_ip)
async def upload_venue_photo(
    request: Request,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
    storage: ObjectStorage = Depends(get_object_storage),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> UploadResponse:
    require_verified_actor(actor, "uploading images")
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(400, "No account associated with this operator.")
    account = account_repo.get(actor.account_id)
    if account is None:
        raise HTTPException(404, "Venue not found.")

    image = await read_processed_image(file)
    stored = await store_image(
        storage,
        unit_of_work,
        venue_photo_key(actor.account_id, image.extension),
        image.data,
        image.content_type,
    )
    account_repo.save(replace(account, photos=[*account.photos, stored.url]))

    return UploadResponse(url=stored.url, filename=stored.key.rsplit("/", 1)[-1])


@router.post("/uploads/venue-avatar", response_model=UploadResponse)
@limiter.limit("10/hour", key_func=actor_or_ip)
async def upload_venue_avatar(
    request: Request,
    file: UploadFile = File(...),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
    storage: ObjectStorage = Depends(get_object_storage),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> UploadResponse:
    require_verified_actor(actor, "uploading images")
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(400, "No account associated with this operator.")
    account = account_repo.get(actor.account_id)
    if account is None:
        raise HTTPException(404, "Venue not found.")

    image = await read_processed_image(file)
    stored = await store_image(
        storage,
        unit_of_work,
        avatar_key("venues", actor.account_id, image.extension),
        image.data,
        image.content_type,
        account.avatar_url,
        avatar_prefix("venues", actor.account_id),
    )
    account_repo.save(replace(account, avatar_url=stored.url))

    return UploadResponse(url=stored.url, filename=stored.key.rsplit("/", 1)[-1])
