from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_event_recorder, get_shift_offer_service
from apps.api.src.helpers import _now_or, _summary_view
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repository_dependencies import get_organisation_repo, get_shift_repo
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_shift_offers import OfferAnswerRequest, ShiftOfferResponse
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.shift_offer_service import ShiftOfferService
from apps.api.src.services.shift_summary import summarise_shifts

router = APIRouter(tags=["shift offers"])


@router.get("/me/shift-offers", response_model=list[ShiftOfferResponse])
def list_my_offers(
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftOfferService = Depends(get_shift_offer_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
) -> list[ShiftOfferResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    offers = service.list_for_worker(actor.effective_worker_id)
    summaries = summarise_shifts([offer.shift_id for offer in offers], shifts, venues)
    return [_offer_view(offer, summaries) for offer in offers]


@router.post("/me/shift-offers/{offer_id}/accept", response_model=ShiftOfferResponse)
def accept_offer(
    offer_id: str,
    payload: OfferAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftOfferService = Depends(get_shift_offer_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftOfferResponse:
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.effective_worker_id
    try:
        booking = service.accept(offer_id, worker_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "offer.accepted",
        "lifecycle",
        actor=actor,
        subject_type="shift_offer",
        subject_id=offer_id,
        worker_id=worker_id,
        context={"shift_id": booking.shift_id, "booking_id": booking.booking_id},
    )
    return _fresh_view(service, offer_id, worker_id, shifts, venues)


@router.post("/me/shift-offers/{offer_id}/decline", response_model=ShiftOfferResponse)
def decline_offer(
    offer_id: str,
    payload: OfferAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftOfferService = Depends(get_shift_offer_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftOfferResponse:
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.effective_worker_id
    try:
        declined = service.decline(offer_id, worker_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "offer.declined",
        "lifecycle",
        actor=actor,
        subject_type="shift_offer",
        subject_id=offer_id,
        worker_id=worker_id,
        context={"shift_id": declined.shift_id},
    )
    return _fresh_view(service, offer_id, worker_id, shifts, venues)


def _fresh_view(
    service: ShiftOfferService, offer_id: str, worker_id: str,
    shifts: ShiftRepository, venues: OrganisationRepository,
) -> ShiftOfferResponse:
    offer = next(
        item for item in service.list_for_worker(worker_id) if item.offer_id == offer_id
    )
    summaries = summarise_shifts([offer.shift_id], shifts, venues)
    return _offer_view(offer, summaries)


def _offer_view(offer: ShiftOffer, summaries) -> ShiftOfferResponse:
    summary = summaries.get(offer.shift_id)
    return ShiftOfferResponse(
        offer_id=offer.offer_id,
        shift_id=offer.shift_id,
        venue_id=offer.venue_id,
        worker_id=offer.worker_id,
        source=offer.source,
        status=offer.status,
        offered_at=offer.offered_at,
        expires_at=offer.expires_at,
        responded_at=offer.responded_at,
        response_source=offer.response_source,
        shift=_summary_view(summary),
    )
