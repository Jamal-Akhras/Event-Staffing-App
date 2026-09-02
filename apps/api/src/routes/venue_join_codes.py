from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_join_code_service
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_workforce import (
    JoinCodeCreateRequest,
    JoinCodePreviewResponse,
    JoinCodeResponse,
    WorkerRelationshipResponse,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.join_code_service import JoinCodeService, JoinCodeView
from apps.api.src.models.worker_relationship import WorkerRelationship

router = APIRouter(tags=["workforce"])

CODE_PATH = Path(min_length=4, max_length=40)


@router.post("/venues/me/join-codes", response_model=JoinCodeResponse, status_code=201)
def create_join_code(
    payload: JoinCodeCreateRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: JoinCodeService = Depends(get_join_code_service),
) -> JoinCodeResponse:
    venue_id = _venue_of(actor)
    try:
        code = service.create(
            venue_id,
            payload.relationship_type,
            payload.max_redemptions,
            utc_now(),
            actor.user_id,
            default_role=payload.default_role,
            expires_at=payload.expires_at,
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return _code_view(JoinCodeView(code=code, redeemed=0))


@router.get("/venues/me/join-codes", response_model=list[JoinCodeResponse])
def list_join_codes(
    actor: ActorContext = Depends(get_actor_context),
    service: JoinCodeService = Depends(get_join_code_service),
) -> list[JoinCodeResponse]:
    venue_id = _venue_of(actor)
    return [_code_view(view) for view in service.list_for_venue(venue_id)]


@router.delete("/venues/me/join-codes/{code}", response_model=JoinCodeResponse)
def revoke_join_code(
    code: str = CODE_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: JoinCodeService = Depends(get_join_code_service),
) -> JoinCodeResponse:
    venue_id = _venue_of(actor)
    try:
        revoked = service.revoke(code, venue_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return _code_view(revoked)


@router.get("/join-codes/{code}", response_model=JoinCodePreviewResponse)
@limiter.limit("20/hour", key_func=actor_or_ip)
def preview_join_code(
    request: Request,
    code: str = CODE_PATH,
    service: JoinCodeService = Depends(get_join_code_service),
) -> JoinCodePreviewResponse:
    try:
        preview = service.preview(code, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return JoinCodePreviewResponse(
        code=preview.code,
        venue_name=preview.venue_name,
        relationship_type=preview.relationship_type,
        default_role=preview.default_role,
    )


@router.post("/join-codes/{code}/redeem", response_model=WorkerRelationshipResponse)
@limiter.limit("10/hour", key_func=actor_or_ip)
def redeem_join_code(
    request: Request,
    code: str = CODE_PATH,
    actor: ActorContext = Depends(get_actor_context),
    service: JoinCodeService = Depends(get_join_code_service),
) -> WorkerRelationshipResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        relationship = service.redeem(code, actor.effective_worker_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return relationship_view(relationship)


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _code_view(view: JoinCodeView) -> JoinCodeResponse:
    return JoinCodeResponse(
        code=view.code.code,
        venue_id=view.code.venue_id,
        relationship_type=view.code.default_relationship_type,
        default_role=view.code.default_role,
        max_redemptions=view.code.max_redemptions,
        redeemed=view.redeemed,
        expires_at=view.code.expires_at,
        revoked_at=view.code.revoked_at,
        created_at=view.code.created_at,
    )


def relationship_view(relationship: WorkerRelationship) -> WorkerRelationshipResponse:
    return WorkerRelationshipResponse(
        relationship_id=relationship.relationship_id,
        venue_id=relationship.venue_id,
        worker_id=relationship.worker_id,
        relationship_type=relationship.relationship_type,
        status=relationship.status,
        default_role=relationship.default_role,
        agreed_rate=relationship.agreed_rate,
        contracted_hours_per_week=relationship.contracted_hours_per_week,
        start_date=relationship.start_date,
        end_date=relationship.end_date,
        created_at=relationship.created_at,
        updated_at=relationship.updated_at,
    )
