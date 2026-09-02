from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_account_repo, get_market_repo
from apps.api.src.models.account import Account
from apps.api.src.repository_dependencies import get_request_unit_of_work
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.schemas_account import AccountResponse, AccountUpdateRequest
from apps.api.src.services.escalation_policy import policy_from_venue
from apps.api.src.services.notification_preferences import normalize_notification_preferences
from apps.api.src.services.stored_upload import retire_objects_after_commit, venue_photo_prefix
from apps.api.src.storage.object_storage import ObjectStorage
from apps.api.src.storage_dependencies import get_object_storage
from apps.api.src.unit_of_work import RequestUnitOfWork

router = APIRouter(tags=["accounts"])


def _account_view(account: Account) -> AccountResponse:
    return AccountResponse(
        account_id=account.account_id,
        venue_id=account.venue_id,
        organisation_id=account.organisation_id,
        market_id=account.market_id,
        name=account.name,
        country=account.country,
        currency=account.currency,
        created_at=account.created_at,
        venue_type=account.venue_type,
        contact_email=account.contact_email,
        contact_phone=account.contact_phone,
        default_location=account.default_location,
        avatar_url=account.avatar_url,
        photos=list(account.photos),
        notification_preferences=dict(account.notification_preferences),
        escalation_policy=account.escalation_policy,
    )


def _get_account(repo: AccountRepository, account_id: str) -> Account:
    account = repo.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account


@router.get("/accounts/me", response_model=AccountResponse)
@router.get("/venues/me", response_model=AccountResponse)
def get_my_account(
    actor: ActorContext = Depends(get_actor_context),
    repo: AccountRepository = Depends(get_account_repo),
) -> AccountResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=404, detail="No account associated with this user.")
    return _account_view(_get_account(repo, actor.account_id))


@router.put("/accounts/me", response_model=AccountResponse)
@router.put("/venues/me", response_model=AccountResponse)
def update_my_account(
    request: AccountUpdateRequest,
    actor: ActorContext = Depends(get_actor_context),
    repo: AccountRepository = Depends(get_account_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    storage: ObjectStorage = Depends(get_object_storage),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> AccountResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=404, detail="No account associated with this user.")
    account = _get_account(repo, actor.account_id)
    if request.market_id is not None:
        market = market_repo.get(request.market_id)
        if market is None or not market.is_active or market.country != account.country:
            raise HTTPException(status_code=400, detail="Invalid market for this venue.")
    if request.photos is not None:
        if len(request.photos) != len(set(request.photos)):
            raise HTTPException(status_code=400, detail="Venue photos must be unique.")
        if not set(request.photos).issubset(set(account.photos)):
            raise HTTPException(
                status_code=400,
                detail="Venue photos can only be added through the upload endpoint.",
            )

    updated = replace(
        account,
        name=request.name if request.name is not None else account.name,
        venue_type=request.venue_type if request.venue_type is not None else account.venue_type,
        contact_email=request.contact_email if request.contact_email is not None else account.contact_email,
        contact_phone=request.contact_phone if request.contact_phone is not None else account.contact_phone,
        default_location=request.default_location if request.default_location is not None else account.default_location,
        photos=request.photos if request.photos is not None else account.photos,
        notification_preferences=(
            normalize_notification_preferences(request.notification_preferences)
            if request.notification_preferences is not None
            else account.notification_preferences
        ),
        market_id=request.market_id if request.market_id is not None else account.market_id,
        escalation_policy=(
            _validated_escalation_policy(request.escalation_policy)
            if request.escalation_policy is not None
            else account.escalation_policy
        ),
    )
    repo.save(updated)
    removed_urls = set(account.photos) - set(updated.photos)
    retire_objects_after_commit(
        storage,
        unit_of_work,
        removed_urls,
        venue_photo_prefix(account.account_id),
    )
    return _account_view(updated)


def _validated_escalation_policy(policy: dict) -> dict:
    try:
        policy_from_venue(policy)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return policy
