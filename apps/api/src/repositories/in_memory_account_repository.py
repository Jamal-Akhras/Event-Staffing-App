from __future__ import annotations

from typing import Dict

from apps.api.src.models.account import Account
from apps.api.src.repositories.account_repository import AccountRepository


class InMemoryAccountRepository(AccountRepository):
    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}

    def get(self, account_id: str) -> Account | None:
        return self._accounts.get(account_id)

    def save(self, account: Account) -> Account:
        self._accounts[account.account_id] = account
        return account

    def clear(self) -> None:
        self._accounts.clear()
