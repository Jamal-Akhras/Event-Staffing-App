from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_account_repo
from apps.api.src.models.account import Account
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.schemas_account import AccountResponse, AccountUpdateRequest
from apps.api.src.services.notification_preferences import normalize_notification_preferences

router = APIRouter(tags=["accounts"])


def _account_view(account: Account) -> AccountResponse:
    return AccountResponse(
        account_id=account.account_id,
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
    )


def _get_account(repo: AccountRepository, account_id: str) -> Account:
    account = repo.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account


@router.get("/accounts/me", response_model=AccountResponse)
def get_my_account(
    actor: ActorContext = Depends(get_actor_context),
    repo: AccountRepository = Depends(get_account_repo),
) -> AccountResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=404, detail="No account associated with this user.")
    return _account_view(_get_account(repo, actor.account_id))


@router.put("/accounts/me", response_model=AccountResponse)
def update_my_account(
    request: AccountUpdateRequest,
    actor: ActorContext = Depends(get_actor_context),
    repo: AccountRepository = Depends(get_account_repo),
) -> AccountResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=404, detail="No account associated with this user.")
    account = _get_account(repo, actor.account_id)

    updated = replace(
        account,
        name=request.name if request.name is not None else account.name,
        venue_type=request.venue_type if request.venue_type is not None else account.venue_type,
        contact_email=request.contact_email if request.contact_email is not None else account.contact_email,
        contact_phone=request.contact_phone if request.contact_phone is not None else account.contact_phone,
        default_location=request.default_location if request.default_location is not None else account.default_location,
        avatar_url=request.avatar_url if request.avatar_url is not None else account.avatar_url,
        photos=request.photos if request.photos is not None else account.photos,
        notification_preferences=(
            normalize_notification_preferences(request.notification_preferences)
            if request.notification_preferences is not None
            else account.notification_preferences
        ),
    )
    repo.save(updated)
    return _account_view(updated)
