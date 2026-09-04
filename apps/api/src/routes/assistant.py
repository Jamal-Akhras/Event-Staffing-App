from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_assistant_service, get_event_recorder
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repository_dependencies import get_worker_profile_repo
from apps.api.src.schemas_assistant import (
    OfferMessageRequest,
    OfferMessageResponse,
    OnboardingResponse,
    OnboardingStepResponse,
    ShiftPostRequest,
    ShiftPostResponse,
)
from apps.api.src.services.assistant.assistant_service import AssistantService
from apps.api.src.services.event_recorder import EventRecorder

router = APIRouter(tags=["assistant"])


@router.post("/assistant/onboarding", response_model=OnboardingResponse)
@limiter.limit("60/hour", key_func=actor_or_ip)
def onboarding(
    request: Request,
    actor: ActorContext = Depends(get_actor_context),
    service: AssistantService = Depends(get_assistant_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> OnboardingResponse:
    venue_id = _venue(actor)
    _audit(recorder, actor, "onboarding")
    guidance = service.onboarding(venue_id, actor.organisation_id or venue_id, utc_now())
    return OnboardingResponse(
        steps=[OnboardingStepResponse(**step.__dict__) for step in guidance.steps],
        summary=guidance.summary,
    )


@router.post("/assistant/shift-post", response_model=ShiftPostResponse)
@limiter.limit("60/hour", key_func=actor_or_ip)
def shift_post(
    request: Request,
    payload: ShiftPostRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: AssistantService = Depends(get_assistant_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftPostResponse:
    venue_id = _venue(actor)
    _audit(recorder, actor, "shift_post")
    draft = service.shift_post(
        venue_id, payload.role, payload.location, payload.start_time, payload.end_time,
        payload.pay_rate, payload.note,
    )
    return ShiftPostResponse(
        description=draft.description,
        suggested_pay_low=draft.suggested_pay_low,
        suggested_pay_high=draft.suggested_pay_high,
        pay_basis=draft.pay_basis,
    )


@router.post("/assistant/offer-message", response_model=OfferMessageResponse)
@limiter.limit("60/hour", key_func=actor_or_ip)
def offer_message(
    request: Request,
    payload: OfferMessageRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: AssistantService = Depends(get_assistant_service),
    workers: WorkerProfileRepository = Depends(get_worker_profile_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> OfferMessageResponse:
    venue_id = _venue(actor)
    profile = workers.get(payload.worker_id)
    worker_name = profile.display_name if profile and profile.display_name else "there"
    _audit(recorder, actor, "offer_message")
    draft = service.offer_message(
        venue_id, worker_name, payload.role, payload.start_time, payload.pay_rate
    )
    return OfferMessageResponse(message=draft.message)


def _venue(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _audit(recorder: EventRecorder, actor: ActorContext, kind: str) -> None:
    recorder.record(
        f"assistant.{kind}",
        "audit",
        actor=actor,
        subject_type="assistant",
        subject_id=kind,
        context={"kind": kind},
    )
