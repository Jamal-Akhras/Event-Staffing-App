from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.assistant.deidentify import deidentify, rehydrate
from apps.api.src.services.assistant.provider import (
    OFFER_MESSAGE,
    SHIFT_POST,
    AssistantProvider,
)
from apps.api.src.services.billing_math import money

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class OnboardingStep:
    key: str
    title: str
    detail: str
    done: bool


@dataclass(frozen=True)
class OnboardingGuidance:
    steps: list[OnboardingStep]
    summary: str


@dataclass(frozen=True)
class ShiftPostDraft:
    description: str
    suggested_pay_low: Decimal | None
    suggested_pay_high: Decimal | None
    pay_basis: str


@dataclass(frozen=True)
class OfferMessageDraft:
    message: str


class AssistantService:
    def __init__(
        self,
        provider: AssistantProvider,
        shifts: ShiftRepository,
        relationships: WorkerRelationshipRepository,
        organisations: OrganisationRepository,
    ) -> None:
        self._provider = provider
        self._shifts = shifts
        self._relationships = relationships
        self._organisations = organisations

    def onboarding(self, venue_id: str, organisation_id: str, now: datetime) -> OnboardingGuidance:
        venues = self._organisations.list_venues_for_organisation(organisation_id)
        team = [
            rel
            for rel in self._relationships.list_for_venue(venue_id, "active")
            if rel.relationship_type in ("permanent", "part_time", "bank")
        ]
        recent = self._shifts.list_in_range(venue_id, now - timedelta(days=30), now + timedelta(days=30))
        steps = [
            OnboardingStep(
                "venue", "Set up your venue",
                "Add your default location, contact details and week-start.",
                len(venues) >= 1,
            ),
            OnboardingStep(
                "team", "Add your staff",
                "Invite permanent and part-time staff with a join code so their shifts are fee-free.",
                len(team) >= 1,
            ),
            OnboardingStep(
                "shift", "Post your first shift",
                "Post a shift or build a rota; unfilled slots escalate to your pool then the market.",
                len(recent) >= 1,
            ),
        ]
        pending = [step for step in steps if not step.done]
        summary = (
            "You're all set — post shifts and manage your week."
            if not pending
            else f"Next: {pending[0].title.lower()}."
        )
        return OnboardingGuidance(steps=steps, summary=summary)

    def shift_post(
        self,
        venue_id: str,
        role: str,
        location: str,
        start_time: datetime,
        end_time: datetime,
        pay_rate: Decimal | None,
        note: str | None,
    ) -> ShiftPostDraft:
        venue = self._organisations.get_venue(venue_id)
        low, high, basis = self._pay_suggestion(venue_id, role, pay_rate)
        deid = deidentify(
            {
                "role": role,
                "venue": venue.name if venue is not None else "your venue",
                "location": location,
                "timing": _timing(start_time, end_time),
                "day": start_time.strftime("%A"),
                "rate": f"£{money(pay_rate)}" if pay_rate is not None else None,
                "note": note.strip() if note else None,
            }
        )
        text = self._provider.generate(SHIFT_POST, deid.fields)
        return ShiftPostDraft(
            description=rehydrate(text, deid.rehydration),
            suggested_pay_low=low,
            suggested_pay_high=high,
            pay_basis=basis,
        )

    def offer_message(
        self, venue_id: str, worker_name: str, role: str, start_time: datetime, pay_rate: Decimal
    ) -> OfferMessageDraft:
        venue = self._organisations.get_venue(venue_id)
        deid = deidentify(
            {
                "worker": worker_name,
                "role": role,
                "date": f"{start_time.strftime('%A')} {start_time.day} {start_time.strftime('%B')}",
                "time": _clock(start_time),
                "venue": venue.name if venue is not None else "us",
                "rate": f"£{money(pay_rate)}",
            }
        )
        text = self._provider.generate(OFFER_MESSAGE, deid.fields)
        return OfferMessageDraft(message=rehydrate(text, deid.rehydration))

    def _pay_suggestion(
        self, venue_id: str, role: str, requested: Decimal | None
    ) -> tuple[Decimal | None, Decimal | None, str]:
        history = [
            shift.pay_rate
            for shift in self._shifts.list_for_account(venue_id, limit=200)
            if shift.role.strip().casefold() == role.strip().casefold() and shift.pay_rate
        ]
        if not history:
            return None, None, "No history for this role yet — set a rate you're comfortable with."
        ordered = sorted(Decimal(rate) for rate in history)
        mid = ordered[len(ordered) // 2]
        low = money(mid * Decimal("0.95"))
        high = money(mid * Decimal("1.10"))
        return low, high, f"Based on your {len(ordered)} recent {role} shift(s), median £{money(mid)}."


def _clock(moment: datetime) -> str:
    hour12 = moment.hour % 12 or 12
    suffix = "am" if moment.hour < 12 else "pm"
    return f"{hour12}:{moment.minute:02d}{suffix}"


def _timing(start_time: datetime, end_time: datetime) -> str:
    hours = round((end_time - start_time).total_seconds() / 3600)
    part = "evening"
    hour = start_time.hour
    if hour < 12:
        part = "morning"
    elif hour < 17:
        part = "afternoon"
    return f"{hours}-hour {part}"
