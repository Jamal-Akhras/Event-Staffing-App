from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol

from apps.api.src.models.venue_join_code import VenueJoinCode, VenueJoinCodeRedemption


class JoinCodeExhaustedError(Exception):
    pass


class VenueJoinCodeRepository(Protocol):
    def save_code(self, code: VenueJoinCode) -> VenueJoinCode: ...

    def get_code(self, code: str) -> VenueJoinCode | None: ...

    def list_codes_for_venue(self, venue_id: str) -> list[VenueJoinCode]: ...

    def count_redemptions(self, code: str) -> int: ...

    def list_redemptions(self, code: str) -> list[VenueJoinCodeRedemption]: ...

    def save_redemption(self, redemption: VenueJoinCodeRedemption) -> VenueJoinCodeRedemption: ...

    def redemption_guard(self, code: str, max_redemptions: int) -> AbstractContextManager[None]: ...
