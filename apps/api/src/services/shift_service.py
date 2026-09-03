from __future__ import annotations

from datetime import datetime

from dataclasses import replace
from uuid import uuid4

from apps.api.src.datetime_utils import utc_now
from apps.api.src.datetime_utils import _now_or
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas import ShiftCreateRequest
from apps.api.src.services.errors import NotFoundError


class ShiftService:
    def __init__(self, repo: ShiftRepository) -> None:
        self._repo = repo

    def create_shift(
        self,
        request: ShiftCreateRequest,
        operator_id: str,
        account_id: str | None = None,
        currency: str = "GBP",
    ) -> Shift:
        now = _now_or(request.now)
        shift = Shift(
            shift_id=str(uuid4()),
            operator_id=operator_id,
            role=request.role,
            location=request.location,
            start_time=request.start_time,
            end_time=request.end_time,
            pay_rate=request.pay_rate,
            notes=request.notes,
            status="open",
            created_at=now,
            updated_at=now,
            workers_needed=request.workers_needed,
            workers_filled=0,
            account_id=account_id,
            currency=currency,
            latitude=None,
            longitude=None,
        )
        return self._repo.save(shift)

    def list_shifts(
        self,
        limit: int = 50,
        role: str | None = None,
        location: str | None = None,
        account_id: str | None = None,
        starts_from: datetime | None = None,
        starts_before: datetime | None = None,
    ) -> list[Shift]:
        if account_id and starts_from and starts_before:
            items = self._repo.list_in_range(account_id, starts_from, starts_before)
        elif account_id:
            items = self._repo.list_for_account(account_id, limit)
        else:
            items = self._repo.list_recent(limit)
        if role:
            items = [item for item in items if item.role == role]
        if location:
            items = [item for item in items if item.location == location]
        return items

    def get_shift(self, shift_id: str) -> Shift:
        shift = self._repo.get(shift_id)
        if shift is None:
            raise NotFoundError("Shift not found.")
        return shift

    def clone_shift(self, shift_id: str) -> Shift:
        original = self.get_shift(shift_id)
        now = utc_now()
        cloned = replace(
            original,
            shift_id=str(uuid4()),
            status="open",
            created_at=now,
            updated_at=now,
            workers_filled=0,
            closed_at=None,
            cancelled_at=None,
            cancellation_reason=None,
            cancelled_by_user_id=None,
        )
        return self._repo.save(cloned)
