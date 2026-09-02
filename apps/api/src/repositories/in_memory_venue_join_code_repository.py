from __future__ import annotations

import threading
from contextlib import contextmanager

from apps.api.src.models.venue_join_code import VenueJoinCode, VenueJoinCodeRedemption
from apps.api.src.repositories.venue_join_code_repository import JoinCodeExhaustedError


class InMemoryVenueJoinCodeRepository:
    def __init__(self) -> None:
        self._codes: dict[str, VenueJoinCode] = {}
        self._redemptions: list[VenueJoinCodeRedemption] = []
        self._redeem_lock = threading.Lock()

    def save_code(self, code: VenueJoinCode) -> VenueJoinCode:
        self._codes[code.code] = code
        return code

    def get_code(self, code: str) -> VenueJoinCode | None:
        return self._codes.get(code)

    def list_codes_for_venue(self, venue_id: str) -> list[VenueJoinCode]:
        return sorted(
            (item for item in self._codes.values() if item.venue_id == venue_id),
            key=lambda item: item.created_at,
        )

    def count_redemptions(self, code: str) -> int:
        return sum(1 for redemption in self._redemptions if redemption.code == code)

    def list_redemptions(self, code: str) -> list[VenueJoinCodeRedemption]:
        return sorted(
            (redemption for redemption in self._redemptions if redemption.code == code),
            key=lambda redemption: redemption.redeemed_at,
        )

    def save_redemption(self, redemption: VenueJoinCodeRedemption) -> VenueJoinCodeRedemption:
        self._redemptions.append(redemption)
        return redemption

    @contextmanager
    def redemption_guard(self, code: str, max_redemptions: int):
        with self._redeem_lock:
            if self.count_redemptions(code) >= max_redemptions:
                raise JoinCodeExhaustedError(code)
            yield

    def clear(self) -> None:
        self._codes.clear()
        self._redemptions.clear()
