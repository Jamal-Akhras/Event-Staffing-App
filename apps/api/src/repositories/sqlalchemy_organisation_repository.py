from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.tenancy_models import (
    OrganisationMembershipModel,
    OrganisationModel,
    VenueModel,
)
from apps.api.src.models.organisation import (
    Organisation,
    OrganisationMembership,
    OrganisationRole,
    Venue,
)
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.services.notification_preferences import normalize_notification_preferences


class SqlAlchemyOrganisationRepository(OrganisationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_organisation(self, organisation_id: str) -> Organisation | None:
        row = self._session.get(OrganisationModel, organisation_id)
        return _organisation(row) if row else None

    def get_venue(self, venue_id: str) -> Venue | None:
        row = self._session.get(VenueModel, venue_id)
        return _venue(row) if row else None

    def get_membership(self, organisation_id: str, user_id: str) -> OrganisationMembership | None:
        row = self._session.get(OrganisationMembershipModel, (organisation_id, user_id))
        return _membership(row) if row else None

    def list_venues_for_user(self, user_id: str) -> list[Venue]:
        statement = (
            select(VenueModel)
            .join(
                OrganisationMembershipModel,
                OrganisationMembershipModel.organisation_id == VenueModel.organisation_id,
            )
            .where(OrganisationMembershipModel.user_id == user_id)
            .order_by(VenueModel.created_at, VenueModel.venue_id)
        )
        return [_venue(row) for row in self._session.scalars(statement)]

    def save_organisation(self, organisation: Organisation) -> Organisation:
        row = self._session.get(OrganisationModel, organisation.organisation_id)
        if row is None:
            row = OrganisationModel(organisation_id=organisation.organisation_id)
            self._session.add(row)
        row.name = organisation.name
        row.country = organisation.country
        row.currency = organisation.currency
        row.created_at = organisation.created_at
        self._session.flush()
        return _organisation(row)

    def save_venue(self, venue: Venue) -> Venue:
        row = self._session.get(VenueModel, venue.venue_id)
        if row is None:
            row = VenueModel(venue_id=venue.venue_id)
            self._session.add(row)
        row.organisation_id = venue.organisation_id
        row.market_id = venue.market_id
        row.name = venue.name
        row.country = venue.country
        row.currency = venue.currency
        row.created_at = venue.created_at
        row.venue_type = venue.venue_type
        row.contact_email = venue.contact_email
        row.contact_phone = venue.contact_phone
        row.default_location = venue.default_location
        row.avatar_url = venue.avatar_url
        row.photos = list(venue.photos)
        row.notification_preferences = dict(venue.notification_preferences)
        self._session.flush()
        return _venue(row)

    def save_membership(self, membership: OrganisationMembership) -> OrganisationMembership:
        key = (membership.organisation_id, membership.user_id)
        row = self._session.get(OrganisationMembershipModel, key)
        if row is None:
            row = OrganisationMembershipModel(
                organisation_id=membership.organisation_id,
                user_id=membership.user_id,
            )
            self._session.add(row)
        row.role = membership.role.value
        row.venue_scope = list(membership.venue_scope) if membership.venue_scope else None
        row.created_at = membership.created_at
        self._session.flush()
        return _membership(row)

    def list_memberships(self, organisation_id: str) -> list[OrganisationMembership]:
        rows = (
            self._session.query(OrganisationMembershipModel)
            .filter(OrganisationMembershipModel.organisation_id == organisation_id)
            .order_by(OrganisationMembershipModel.created_at)
            .all()
        )
        return [_membership(row) for row in rows]

    def delete_membership(self, organisation_id: str, user_id: str) -> bool:
        row = self._session.get(OrganisationMembershipModel, (organisation_id, user_id))
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def list_venues_for_organisation(self, organisation_id: str) -> list[Venue]:
        rows = (
            self._session.query(VenueModel)
            .filter(VenueModel.organisation_id == organisation_id)
            .order_by(VenueModel.created_at, VenueModel.venue_id)
            .all()
        )
        return [_venue(row) for row in rows]


def _organisation(row: OrganisationModel) -> Organisation:
    return Organisation(
        organisation_id=row.organisation_id,
        name=row.name,
        country=row.country,
        currency=row.currency,
        created_at=row.created_at,
    )


def _venue(row: VenueModel) -> Venue:
    return Venue(
        venue_id=row.venue_id,
        organisation_id=row.organisation_id,
        name=row.name,
        country=row.country,
        currency=row.currency,
        created_at=row.created_at,
        venue_type=row.venue_type,
        contact_email=row.contact_email,
        contact_phone=row.contact_phone,
        default_location=row.default_location,
        avatar_url=row.avatar_url,
        photos=list(row.photos or []),
        notification_preferences=normalize_notification_preferences(row.notification_preferences),
        market_id=row.market_id,
    )


def _membership(row: OrganisationMembershipModel) -> OrganisationMembership:
    return OrganisationMembership(
        organisation_id=row.organisation_id,
        user_id=row.user_id,
        role=OrganisationRole(row.role),
        created_at=row.created_at,
        venue_scope=tuple(row.venue_scope) if row.venue_scope else None,
    )
