from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.auth.permissions import MANAGE_BILLING, require_permission
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_billing_service, get_organisation_repo, get_people_service
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.routes.venue_people import _entry_view
from apps.api.src.schemas_organisation_overview import (
    OrgBillingSummaryResponse,
    OrgStaffEntryResponse,
    OrgVenueBillingResponse,
)
from apps.api.src.services.billing_service import BillingService
from apps.api.src.services.people_service import PeopleService

router = APIRouter(tags=["organisation overview"])


@router.get("/organisations/me/staff", response_model=list[OrgStaffEntryResponse])
def list_organisation_staff(
    actor: ActorContext = Depends(get_actor_context),
    organisations: OrganisationRepository = Depends(get_organisation_repo),
    people: PeopleService = Depends(get_people_service),
) -> list[OrgStaffEntryResponse]:
    venues = _covered_venues(actor, organisations)
    now = utc_now()
    entries: list[OrgStaffEntryResponse] = []
    for venue in venues:
        for entry in people.directory(venue.venue_id, now):
            entries.append(
                OrgStaffEntryResponse(
                    venue_id=venue.venue_id,
                    venue_name=venue.name,
                    person=_entry_view(entry),
                )
            )
    return entries


@router.get("/organisations/me/billing/summary", response_model=OrgBillingSummaryResponse)
def organisation_billing_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    actor: ActorContext = Depends(get_actor_context),
    organisations: OrganisationRepository = Depends(get_organisation_repo),
    billing: BillingService = Depends(get_billing_service),
) -> OrgBillingSummaryResponse:
    require_permission(actor, MANAGE_BILLING)
    venues = _covered_venues(actor, organisations)
    period = month or utc_now().strftime("%Y-%m")
    now = utc_now()
    rows: list[OrgVenueBillingResponse] = []
    wages_total = Decimal("0.00")
    fee_total = Decimal("0.00")
    for venue in venues:
        summary = billing.summary(venue.venue_id, period, now)
        rows.append(
            OrgVenueBillingResponse(
                venue_id=venue.venue_id,
                venue_name=venue.name,
                wages_total=summary.wages_total,
                fee_total=summary.fee_total,
                amount_due=summary.amount_due,
            )
        )
        wages_total += summary.wages_total
        fee_total += summary.fee_total
    return OrgBillingSummaryResponse(
        month=period,
        venues=rows,
        wages_total=wages_total,
        fee_total=fee_total,
        amount_due=fee_total,
    )


def _covered_venues(actor: ActorContext, organisations: OrganisationRepository):
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.organisation_id:
        raise HTTPException(status_code=403, detail="This account has no organisation.")
    venues = organisations.list_venues_for_organisation(actor.organisation_id)
    if actor.venue_scope is not None:
        venues = [venue for venue in venues if venue.venue_id in actor.venue_scope]
    return venues
