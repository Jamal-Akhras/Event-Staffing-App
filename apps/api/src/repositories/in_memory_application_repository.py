from __future__ import annotations

from typing import Dict

from apps.api.src.models.application import Application
from apps.api.src.repositories.application_repository import DuplicateApplicationError
from apps.api.src.repositories.shift_repository import ShiftRepository


class InMemoryApplicationRepository:
    def __init__(self) -> None:
        self._applications: Dict[str, Application] = {}
        self._shift_repo: ShiftRepository | None = None

    def attach_shift_repo(self, shift_repo: ShiftRepository) -> None:
        self._shift_repo = shift_repo

    def get(self, application_id: str) -> Application | None:
        return self._applications.get(application_id)

    def save(self, application: Application) -> Application:
        existing = self.find_by_worker_and_shift(application.worker_id, application.shift_id)
        if existing is not None and existing.application_id != application.application_id:
            raise DuplicateApplicationError("Worker has already applied to this shift.")
        self._applications[application.application_id] = application
        return application

    def list_recent(
        self,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        return self._list(limit, status=status, shift_id=shift_id)

    def list_by_worker(
        self,
        worker_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[Application]:
        return self._list(
            limit,
            worker_id=worker_id,
            operator_id=operator_id,
            status=status,
            shift_id=shift_id,
        )

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        return self._list(
            limit,
            worker_id=worker_id,
            operator_id=operator_id,
            status=status,
            shift_id=shift_id,
        )

    def list_for_account(
        self,
        account_id: str,
        limit: int = 50,
        status: str | None = None,
        shift_id: str | None = None,
        worker_id: str | None = None,
    ) -> list[Application]:
        if self._shift_repo is None:
            raise RuntimeError("InMemoryApplicationRepository requires a shift repo to list by account.")
        account_shift_ids = {shift.shift_id for shift in self._shift_repo.list_for_account(account_id, limit=10_000)}
        items = [item for item in self._applications.values() if item.shift_id in account_shift_ids]
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        if status:
            items = [item for item in items if item.status == status]
        if shift_id:
            items = [item for item in items if item.shift_id == shift_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def find_by_worker_and_shift(self, worker_id: str, shift_id: str) -> Application | None:
        for application in self._applications.values():
            if application.worker_id == worker_id and application.shift_id == shift_id:
                return application
        return None

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Application]:
        return self._list(10_000, shift_id=shift_id)

    def clear(self) -> None:
        self._applications.clear()

    def _list(
        self,
        limit: int,
        worker_id: str | None = None,
        operator_id: str | None = None,
        status: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        items = list(self._applications.values())
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        if operator_id:
            items = [item for item in items if item.operator_id == operator_id]
        if status:
            items = [item for item in items if item.status == status]
        if shift_id:
            items = [item for item in items if item.shift_id == shift_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]
