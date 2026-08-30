from __future__ import annotations

from typing import Protocol

from apps.api.src.models.application import Application
from apps.api.src.models.insights import PendingSummary


class DuplicateApplicationError(Exception):
    pass


class ApplicationRepository(Protocol):
    def get(self, application_id: str) -> Application | None:
        ...

    def save(self, application: Application) -> Application:
        ...

    def list_recent(
        self,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        ...

    def list_by_worker(
        self,
        worker_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[Application]:
        ...

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        ...

    def list_for_account(
        self,
        account_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        ...

    def find_by_worker_and_shift(self, worker_id: str, shift_id: str) -> Application | None:
        ...

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Application]:
        ...

    def list_for_shifts(self, shift_ids: list[str]) -> list[Application]:
        ...

    def pending_summary(self, account_id: str) -> PendingSummary:
        ...
