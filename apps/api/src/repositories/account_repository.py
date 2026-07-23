from __future__ import annotations

from abc import ABC, abstractmethod

from apps.api.src.models.account import Account


class AccountRepository(ABC):
    @abstractmethod
    def get(self, account_id: str) -> Account | None: ...

    @abstractmethod
    def save(self, account: Account) -> Account: ...
