from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.venue_join_code import VenueJoinCode, VenueJoinCodeRedemption
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES, WorkerRelationship
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.venue_join_code_repository import (
    JoinCodeExhaustedError,
    VenueJoinCodeRepository,
)
from apps.api.src.services.code_generation import new_code
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.relationship_service import RelationshipService

CODE_PREFIX = "TEAM"


@dataclass(frozen=True)
class JoinCodeView:
    code: VenueJoinCode
    redeemed: int


@dataclass(frozen=True)
class JoinCodePreview:
    code: str
    venue_name: str
    relationship_type: str
    default_role: str | None


class JoinCodeService:
    def __init__(
        self,
        codes: VenueJoinCodeRepository,
        relationships: RelationshipService,
        accounts: AccountRepository,
    ) -> None:
        self._codes = codes
        self._relationships = relationships
        self._accounts = accounts

    def create(
        self,
        venue_id: str,
        relationship_type: str,
        max_redemptions: int,
        now: datetime,
        actor_user_id: str,
        default_role: str | None = None,
        expires_at: datetime | None = None,
    ) -> VenueJoinCode:
        if relationship_type not in EMPLOYED_TYPES:
            raise ValidationError(
                "A join code can only add employed staff. Pool membership is offered by the venue "
                "after a worker has completed a shift."
            )
        if max_redemptions < 1:
            raise ValidationError("A join code needs at least one redemption.")
        if expires_at is not None and expires_at <= now:
            raise ValidationError("The expiry date has to be in the future.")
        return self._codes.save_code(
            VenueJoinCode(
                code=new_code(CODE_PREFIX),
                venue_id=venue_id,
                default_relationship_type=relationship_type,
                max_redemptions=max_redemptions,
                created_at=now,
                created_by_user_id=actor_user_id,
                default_role=default_role,
                expires_at=expires_at,
            )
        )

    def list_for_venue(self, venue_id: str) -> list[JoinCodeView]:
        return [
            JoinCodeView(code=code, redeemed=self._codes.count_redemptions(code.code))
            for code in self._codes.list_codes_for_venue(venue_id)
        ]

    def revoke(self, code: str, venue_id: str, now: datetime) -> JoinCodeView:
        found = self._for_venue(code, venue_id)
        if found.revoked_at is None:
            found = self._codes.save_code(replace(found, revoked_at=now))
        return JoinCodeView(code=found, redeemed=self._codes.count_redemptions(found.code))

    def preview(self, code: str, now: datetime) -> JoinCodePreview:
        found = self._usable(code, now)
        venue = self._accounts.get(found.venue_id)
        if venue is None:
            raise NotFoundError("That code belongs to a venue that no longer exists.")
        return JoinCodePreview(
            code=found.code,
            venue_name=venue.name,
            relationship_type=found.default_relationship_type,
            default_role=found.default_role,
        )

    def redeem(self, code: str, worker_id: str, now: datetime) -> WorkerRelationship:
        known = self._codes.get_code(code.strip().upper())
        if known is None:
            raise NotFoundError("That join code was not found.")

        redeemed_before = any(
            item.worker_id == worker_id for item in self._codes.list_redemptions(known.code)
        )
        if redeemed_before:
            existing = self._relationships.get(known.venue_id, worker_id)
            if existing is not None:
                return existing

        found = self._usable(code, now)
        try:
            with self._codes.redemption_guard(found.code, found.max_redemptions):
                relationship = self._relationships.establish(
                    found.venue_id,
                    worker_id,
                    found.default_relationship_type,
                    now,
                    reason=f"Joined with code {found.code}.",
                    default_role=found.default_role,
                )
                self._save_redemption(found, worker_id, relationship.relationship_id, now)
        except JoinCodeExhaustedError:
            raise ValidationError("That join code has already been used the maximum number of times.")
        return relationship

    def _save_redemption(self, found, worker_id: str, relationship_id: str, now):
        self._codes.save_redemption(
            VenueJoinCodeRedemption(
                redemption_id=str(uuid4()),
                code=found.code,
                venue_id=found.venue_id,
                worker_id=worker_id,
                relationship_id=relationship_id,
                redeemed_at=now,
            )
        )

    def _for_venue(self, code: str, venue_id: str) -> VenueJoinCode:
        found = self._codes.get_code(code.strip().upper())
        if found is None or found.venue_id != venue_id:
            raise NotFoundError("That join code was not found.")
        return found

    def _usable(self, code: str, now: datetime) -> VenueJoinCode:
        found = self._codes.get_code(code.strip().upper())
        if found is None:
            raise NotFoundError("That join code was not found.")
        if found.revoked_at is not None:
            raise ValidationError("That join code has been turned off by the venue.")
        if found.expires_at is not None and found.expires_at <= now:
            raise ValidationError("That join code has expired.")
        if self._codes.count_redemptions(found.code) >= found.max_redemptions:
            raise ValidationError("That join code has already been used the maximum number of times.")
        return found
