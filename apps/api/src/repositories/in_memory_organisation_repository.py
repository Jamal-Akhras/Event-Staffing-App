from __future__ import annotations

from apps.api.src.models.account import Account
from apps.api.src.models.organisation import Organisation, OrganisationMembership, Venue
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository


class InMemoryOrganisationRepository(OrganisationRepository):
    def __init__(self, accounts: InMemoryAccountRepository | None = None) -> None:
        self._organisations: dict[str, Organisation] = {}
        self._venues: dict[str, Venue] = {}
        self._memberships: dict[tuple[str, str], OrganisationMembership] = {}
        self._accounts = accounts

    def get_organisation(self, organisation_id: str) -> Organisation | None:
        return self._organisations.get(organisation_id)

    def get_venue(self, venue_id: str) -> Venue | None:
        return self._venues.get(venue_id)

    def get_membership(self, organisation_id: str, user_id: str) -> OrganisationMembership | None:
        return self._memberships.get((organisation_id, user_id))

    def list_venues_for_user(self, user_id: str) -> list[Venue]:
        organisation_ids = {
            membership.organisation_id
            for membership in self._memberships.values()
            if membership.user_id == user_id
        }
        return sorted(
            (venue for venue in self._venues.values() if venue.organisation_id in organisation_ids),
            key=lambda venue: (venue.created_at, venue.venue_id),
        )

    def save_organisation(self, organisation: Organisation) -> Organisation:
        self._organisations[organisation.organisation_id] = organisation
        return organisation

    def save_venue(self, venue: Venue) -> Venue:
        self._venues[venue.venue_id] = venue
        if self._accounts is not None:
            self._accounts.save(
                Account(
                    account_id=venue.venue_id,
                    organisation_id=venue.organisation_id,
                    market_id=venue.market_id,
                    name=venue.name,
                    country=venue.country,
                    currency=venue.currency,
                    created_at=venue.created_at,
                    venue_type=venue.venue_type,
                    contact_email=venue.contact_email,
                    contact_phone=venue.contact_phone,
                    default_location=venue.default_location,
                    avatar_url=venue.avatar_url,
                    photos=list(venue.photos),
                    notification_preferences=dict(venue.notification_preferences),
                )
            )
        return venue

    def save_membership(self, membership: OrganisationMembership) -> OrganisationMembership:
        self._memberships[(membership.organisation_id, membership.user_id)] = membership
        return membership

    def list_memberships(self, organisation_id: str) -> list[OrganisationMembership]:
        rows = [
            membership
            for membership in self._memberships.values()
            if membership.organisation_id == organisation_id
        ]
        return sorted(rows, key=lambda membership: membership.created_at)

    def delete_membership(self, organisation_id: str, user_id: str) -> bool:
        return self._memberships.pop((organisation_id, user_id), None) is not None

    def list_venues_for_organisation(self, organisation_id: str) -> list[Venue]:
        return sorted(
            (venue for venue in self._venues.values() if venue.organisation_id == organisation_id),
            key=lambda venue: (venue.created_at, venue.venue_id),
        )

    def clear(self) -> None:
        self._organisations.clear()
        self._venues.clear()
        self._memberships.clear()
