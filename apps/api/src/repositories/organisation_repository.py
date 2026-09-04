from __future__ import annotations

from abc import ABC, abstractmethod

from apps.api.src.models.organisation import Organisation, OrganisationMembership, Venue


class OrganisationRepository(ABC):
    @abstractmethod
    def get_organisation(self, organisation_id: str) -> Organisation | None: ...

    @abstractmethod
    def get_venue(self, venue_id: str) -> Venue | None: ...

    @abstractmethod
    def get_membership(self, organisation_id: str, user_id: str) -> OrganisationMembership | None: ...

    @abstractmethod
    def list_venues_for_user(self, user_id: str) -> list[Venue]: ...

    @abstractmethod
    def save_organisation(self, organisation: Organisation) -> Organisation: ...

    @abstractmethod
    def save_venue(self, venue: Venue) -> Venue: ...

    @abstractmethod
    def save_membership(self, membership: OrganisationMembership) -> OrganisationMembership: ...

    def list_memberships(self, organisation_id: str) -> list[OrganisationMembership]: ...

    def delete_membership(self, organisation_id: str, user_id: str) -> bool: ...

    def list_venues_for_organisation(self, organisation_id: str) -> list[Venue]: ...
