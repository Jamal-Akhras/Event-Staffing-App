from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.config import get_bool_env
from apps.api.src.deps import get_account_repo, get_shift_repo, get_shift_service, get_user_repo
from apps.api.src.helpers import _shift_view
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ErrorResponse, ShiftCreateRequest, ShiftResponse
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.geocoding import geocode
from apps.api.src.services.shift_service import ShiftService

router = APIRouter(tags=["shifts"])


def _geocode_and_update(shift_id: str, location: str, repo: ShiftRepository) -> None:
    lat, lng = geocode(location)
    if lat is None:
        return
    shift = repo.get(shift_id)
    if shift is not None:
        repo.save(replace(shift, latitude=lat, longitude=lng))


def _require_verified_operator(actor: ActorContext, user_repo: UserRepository) -> None:
    """Operators must verify their email before posting shifts.

    Skipped in DEV_MODE because header-based actors have no backing user record.
    Workers are intentionally not gated here — they may use the app while unverified.
    """
    if get_bool_env("DEV_MODE", False):
        return
    user = user_repo.get(actor.user_id)
    if user is None or not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Verify your email before posting shifts. Check your inbox for the verification link.",
        )


@router.post("/shifts", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}})
def create_shift(
    request: ShiftCreateRequest,
    background_tasks: BackgroundTasks,
    service: ShiftService = Depends(get_shift_service),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ShiftResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    _require_verified_operator(actor, user_repo)
    currency = "GBP"
    if actor.account_id:
        account = account_repo.get(actor.account_id)
        if account:
            currency = account.currency
    shift = service.create_shift(request, actor.user_id, actor.account_id, currency)
    background_tasks.add_task(_geocode_and_update, shift.shift_id, shift.location, shift_repo)
    return _shift_view(shift)


@router.get("/shifts", response_model=list[ShiftResponse])
def list_shifts(
    limit: int = 50,
    role: str | None = None,
    location: str | None = None,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[ShiftResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    account_id = actor.account_id if actor.role == ActorRole.OPERATOR else None
    shifts = service.list_shifts(limit, role, location, account_id=account_id)
    if actor.role == ActorRole.WORKER:
        shifts = [item for item in shifts if item.status == "open"]
    return [_shift_view(item) for item in shifts]


@router.get("/shifts/{shift_id}", response_model=ShiftResponse, responses={404: {"model": ErrorResponse}})
def get_shift_by_id(
    shift_id: str,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        shift = service.get_shift(shift_id)
        _require_shift_access(actor, shift)
        return _shift_view(shift)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/clone", response_model=ShiftResponse, responses={404: {"model": ErrorResponse}})
def clone_shift(
    shift_id: str,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        shift = service.get_shift(shift_id)
        require_role(actor.role, {ActorRole.OPERATOR})
        if shift.account_id != actor.account_id:
            raise HTTPException(status_code=403, detail="Operator can only clone their own shifts.")
        return _shift_view(service.clone_shift(shift_id))
    except ServiceError as exc:
        raise_service_error(exc)


def _require_shift_access(actor: ActorContext, shift: Shift) -> None:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if actor.role == ActorRole.OPERATOR and shift.account_id != actor.account_id:
        raise HTTPException(status_code=403, detail="Operator can only access their own shifts.")
    if actor.role == ActorRole.WORKER and shift.status != "open":
        raise HTTPException(status_code=403, detail="Worker can only access open shifts.")
