from __future__ import annotations

import secrets

from datetime import datetime, timedelta
from uuid import uuid4

from apps.api.src.models.manager_invitation import ManagerInvitation
from apps.api.src.models.organisation import (
    Organisation,
    OrganisationMembership,
    OrganisationRole,
    Venue,
    membership_covers,
)
from apps.api.src.repositories.manager_invitation_repository import ManagerInvitationRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.user_repository import UserRepository
import secrets
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from apps.api.src.services.outbox_publisher import OutboxPublisher

INVITATION_DAYS = 7


class OrganisationService:
    def __init__(
        self,
        organisations: OrganisationRepository,
        invitations: ManagerInvitationRepository,
        users: UserRepository,
        markets: MarketRepository,
        outbox: OutboxPublisher,
    ) -> None:
        self._organisations = organisations
        self._invitations = invitations
        self._users = users
        self._markets = markets
        self._outbox = outbox

    def create_venue(
        self,
        organisation_id: str,
        name: str,
        market_id: str,
        venue_type: str | None,
        default_location: str | None,
        now: datetime,
    ) -> Venue:
        organisation = self._require_organisation(organisation_id)
        market = self._markets.get(market_id)
        if market is None or not market.is_active:
            raise ValidationError("Invalid or inactive market.")
        if market.country != organisation.country:
            raise ValidationError("Market does not belong to the organisation's country.")
        venue = Venue(
            venue_id=str(uuid4()),
            organisation_id=organisation_id,
            name=name,
            country=organisation.country,
            currency=market.currency,
            created_at=now,
            venue_type=venue_type,
            default_location=default_location,
            market_id=market_id,
        )
        return self._organisations.save_venue(venue)

    def invite_manager(
        self,
        organisation_id: str,
        email: str,
        role: str,
        venue_scope: tuple[str, ...] | None,
        created_by_user_id: str,
        now: datetime,
    ) -> ManagerInvitation:
        self._require_organisation(organisation_id)
        if venue_scope:
            for venue_id in venue_scope:
                venue = self._organisations.get_venue(venue_id)
                if venue is None or venue.organisation_id != organisation_id:
                    raise ValidationError(f"Venue {venue_id} is not part of this organisation.")
        existing_user = self._users.get_by_email(email)
        if existing_user is not None:
            for membership in self._organisations.list_memberships(organisation_id):
                if membership.user_id == existing_user.user_id:
                    raise ConflictError("That person is already a member of this organisation.")
        invitation = ManagerInvitation(
            invitation_id=str(uuid4()),
            organisation_id=organisation_id,
            email=email,
            role=role,
            venue_scope=venue_scope,
            token=secrets.token_urlsafe(18),
            created_by_user_id=created_by_user_id,
            created_at=now,
            expires_at=now + timedelta(days=INVITATION_DAYS),
        )
        return self._invitations.save(invitation)

    def accept_invitation(self, token: str, user_id: str, now: datetime) -> OrganisationMembership:
        invitation = self._invitations.get_by_token(token)
        if invitation is None:
            raise NotFoundError("That invitation was not found.")
        if not invitation.is_open(now):
            raise ValidationError("This invitation has expired or was already used.")
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        if user.email.lower() != invitation.email.lower():
            raise ValidationError("This invitation was issued to a different email address.")
        if self._organisations.get_membership(invitation.organisation_id, user_id) is not None:
            raise ConflictError("You are already a member of this organisation.")
        membership = self._organisations.save_membership(
            OrganisationMembership(
                organisation_id=invitation.organisation_id,
                user_id=user_id,
                role=OrganisationRole(invitation.role),
                created_at=now,
                venue_scope=invitation.venue_scope,
            )
        )
        self._invitations.save(
            ManagerInvitation(
                invitation_id=invitation.invitation_id,
                organisation_id=invitation.organisation_id,
                email=invitation.email,
                role=invitation.role,
                venue_scope=invitation.venue_scope,
                token=invitation.token,
                created_by_user_id=invitation.created_by_user_id,
                created_at=invitation.created_at,
                expires_at=invitation.expires_at,
                accepted_at=now,
                accepted_user_id=user_id,
            )
        )
        return membership

    def list_members(self, organisation_id: str) -> list[tuple[OrganisationMembership, str | None]]:
        members = []
        for membership in self._organisations.list_memberships(organisation_id):
            user = self._users.get(membership.user_id)
            members.append((membership, user.email if user else None))
        return members

    def change_role(
        self,
        organisation_id: str,
        target_user_id: str,
        role: str,
        venue_scope: tuple[str, ...] | None,
        now: datetime,
    ) -> OrganisationMembership:
        membership = self._organisations.get_membership(organisation_id, target_user_id)
        if membership is None:
            raise NotFoundError("That member was not found.")
        new_role = OrganisationRole(role)
        if membership.role == OrganisationRole.OWNER and new_role != OrganisationRole.OWNER:
            self._require_another_owner(organisation_id, target_user_id)
        if new_role == OrganisationRole.MANAGER and not venue_scope:
            raise ValidationError("A manager needs at least one venue.")
        if new_role != OrganisationRole.MANAGER:
            venue_scope = None
        return self._organisations.save_membership(
            OrganisationMembership(
                organisation_id=organisation_id,
                user_id=target_user_id,
                role=new_role,
                created_at=membership.created_at,
                venue_scope=venue_scope,
            )
        )

    def remove_member(self, organisation_id: str, target_user_id: str) -> None:
        membership = self._organisations.get_membership(organisation_id, target_user_id)
        if membership is None:
            raise NotFoundError("That member was not found.")
        if membership.role == OrganisationRole.OWNER:
            self._require_another_owner(organisation_id, target_user_id)
        self._organisations.delete_membership(organisation_id, target_user_id)

    def default_venue_for(self, membership: OrganisationMembership) -> Venue:
        if membership.venue_scope:
            venue = self._organisations.get_venue(membership.venue_scope[0])
            if venue is not None:
                return venue
        venues = self._organisations.list_venues_for_organisation(membership.organisation_id)
        if not venues:
            raise ValidationError("This organisation has no venues yet.")
        return venues[0]

    def venue_for_switch(self, organisation_id: str, user_id: str, venue_id: str) -> Venue:
        membership = self._organisations.get_membership(organisation_id, user_id)
        venue = self._organisations.get_venue(venue_id)
        if membership is None or venue is None or venue.organisation_id != organisation_id:
            raise NotFoundError("That venue was not found in your organisation.")
        if not membership_covers(membership, venue_id):
            raise ValidationError("Your role does not cover that venue.")
        return venue

    def _require_organisation(self, organisation_id: str) -> Organisation:
        organisation = self._organisations.get_organisation(organisation_id)
        if organisation is None:
            raise NotFoundError("Organisation not found.")
        return organisation

    def _require_another_owner(self, organisation_id: str, excluding_user_id: str) -> None:
        owners = [
            membership
            for membership in self._organisations.list_memberships(organisation_id)
            if membership.role == OrganisationRole.OWNER
            and membership.user_id != excluding_user_id
        ]
        if not owners:
            raise ValidationError("An organisation keeps at least one owner.")
