from __future__ import annotations

from fastapi import Depends

from apps.api.src.auth import ActorContext, get_actor_context
from apps.api.src.deps import get_organisation_repo, get_shift_repo
from apps.api.src.helpers import _application_view, _booking_view
from apps.api.src.models.application import Application
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas import ApplicationResponse, BookingResponse
from apps.api.src.services.shift_summary import summarise_shifts
from packages.domain.src.booking import Booking


class BookingPresenter:
    def __init__(
        self,
        shifts: ShiftRepository,
        venues: OrganisationRepository,
        actor: ActorContext,
    ) -> None:
        self._shifts = shifts
        self._venues = venues
        self._role = actor.role

    def many(self, bookings: list[Booking]) -> list[BookingResponse]:
        summaries = summarise_shifts([item.shift_id for item in bookings], self._shifts, self._venues)
        return [_booking_view(item, self._role, summaries.get(item.shift_id)) for item in bookings]

    def one(self, booking: Booking) -> BookingResponse:
        return self.many([booking])[0]


class ApplicationPresenter:
    def __init__(self, shifts: ShiftRepository, venues: OrganisationRepository) -> None:
        self._shifts = shifts
        self._venues = venues

    def many(self, applications: list[Application]) -> list[ApplicationResponse]:
        summaries = summarise_shifts([item.shift_id for item in applications], self._shifts, self._venues)
        return [_application_view(item, summaries.get(item.shift_id)) for item in applications]

    def one(self, application: Application) -> ApplicationResponse:
        return self.many([application])[0]


def get_booking_presenter(
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingPresenter:
    return BookingPresenter(shifts, venues, actor)


def get_application_presenter(
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
) -> ApplicationPresenter:
    return ApplicationPresenter(shifts, venues)
