from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_template_service
from apps.api.src.helpers import _shift_view
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ErrorResponse,
    GenerateShiftsRequest,
    ShiftResponse,
    TemplateCreateRequest,
    TemplateResponse,
    TemplateUpdateRequest,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.template_service import TemplateService

router = APIRouter(tags=["templates"])


@router.post("/templates", response_model=TemplateResponse, responses={400: {"model": ErrorResponse}})
def create_template(
    request: TemplateCreateRequest,
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> TemplateResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return TemplateResponse(**service.create_template(request, actor.user_id, actor.account_id).model_dump())


@router.get("/templates", response_model=list[TemplateResponse])
def list_templates(
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[TemplateResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    return [TemplateResponse(**t.model_dump()) for t in service.list_templates(actor.user_id)]


@router.get("/templates/{template_id}", response_model=TemplateResponse, responses={404: {"model": ErrorResponse}})
def get_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> TemplateResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        return TemplateResponse(**service.get_template(template_id, actor.user_id).model_dump())
    except ServiceError as exc:
        raise_service_error(exc)


@router.put("/templates/{template_id}", response_model=TemplateResponse, responses={404: {"model": ErrorResponse}})
def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> TemplateResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        return TemplateResponse(**service.update_template(template_id, request, actor.user_id).model_dump())
    except ServiceError as exc:
        raise_service_error(exc)


@router.delete("/templates/{template_id}", responses={404: {"model": ErrorResponse}})
def delete_template(
    template_id: str,
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        service.delete_template(template_id, actor.user_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "deleted", "template_id": template_id}


@router.post("/templates/{template_id}/generate", response_model=list[ShiftResponse], responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
def generate_shifts_from_template(
    template_id: str,
    request: GenerateShiftsRequest,
    service: TemplateService = Depends(get_template_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[ShiftResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        return [_shift_view(s) for s in service.generate_shifts(template_id, request, actor.user_id)]
    except ServiceError as exc:
        raise_service_error(exc)
