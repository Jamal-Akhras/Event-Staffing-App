from __future__ import annotations

from apps.api.src.models.partner_code import PartnerCode, PartnerCodeRedemption


class InMemoryPartnerCodeRepository:
    def __init__(self) -> None:
        self._codes: dict[str, PartnerCode] = {}
        self._redemptions: dict[str, PartnerCodeRedemption] = {}

    def get_code(self, code: str) -> PartnerCode | None:
        return self._codes.get(code)

    def get_code_for_redemption(self, code: str, account_id: str) -> PartnerCode | None:
        return self.get_code(code)

    def save_code(self, partner_code: PartnerCode) -> PartnerCode:
        self._codes[partner_code.code] = partner_code
        return partner_code

    def list_redemptions(self, code: str) -> list[PartnerCodeRedemption]:
        return sorted(
            (item for item in self._redemptions.values() if item.code == code),
            key=lambda item: item.redeemed_at,
        )

    def get_redemption_for_account(self, account_id: str) -> PartnerCodeRedemption | None:
        return next((item for item in self._redemptions.values() if item.account_id == account_id), None)

    def save_redemption(self, redemption: PartnerCodeRedemption) -> PartnerCodeRedemption:
        self._redemptions[redemption.redemption_id] = redemption
        return redemption

    def clear(self) -> None:
        self._codes.clear()
        self._redemptions.clear()
