from __future__ import annotations

from datetime import datetime, time, timedelta
from uuid import uuid4

from apps.api.src.datetime_utils import normalize_utc, utc_now
from apps.api.src.models.shift import Shift
from apps.api.src.models.shift_template import ShiftTemplate
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.template_repository import TemplateRepository
from apps.api.src.schemas import (
    GenerateShiftsRequest,
    TemplateCreateRequest,
    TemplateUpdateRequest,
)
from apps.api.src.services.errors import NotFoundError, ValidationError


class TemplateService:
    def __init__(
        self,
        template_repo: TemplateRepository,
        shift_repo: ShiftRepository,
    ) -> None:
        self._templates = template_repo
        self._shifts = shift_repo

    def create_template(self, request: TemplateCreateRequest, operator_id: str, account_id: str | None = None) -> ShiftTemplate:
        now = utc_now()
        template = ShiftTemplate(
            template_id=f"tmpl_{uuid4().hex}",
            operator_id=operator_id,
            name=request.name,
            role=request.role,
            location=request.location,
            duration_hours=request.duration_hours,
            pay_rate=request.pay_rate,
            workers_needed=request.workers_needed,
            notes=request.notes,
            created_at=now,
            updated_at=now,
            account_id=account_id,
        )
        return self._templates.save_template(template)

    def list_templates(self, operator_id: str) -> list[ShiftTemplate]:
        return self._templates.list_templates(operator_id)

    def get_template(self, template_id: str, operator_id: str) -> ShiftTemplate:
        return self._get_owned_template(template_id, operator_id)

    def update_template(
        self,
        template_id: str,
        request: TemplateUpdateRequest,
        operator_id: str,
    ) -> ShiftTemplate:
        existing = self._get_owned_template(template_id, operator_id)
        updated = existing.model_copy(update={**request.model_dump(), "updated_at": utc_now()})
        return self._templates.save_template(updated)

    def delete_template(self, template_id: str, operator_id: str) -> bool:
        self._get_owned_template(template_id, operator_id)
        return self._templates.delete_template(template_id)

    def generate_shifts(
        self,
        template_id: str,
        request: GenerateShiftsRequest,
        operator_id: str,
    ) -> list[Shift]:
        template = self._get_owned_template(template_id, operator_id)
        hour, minute = self._parse_start_time(request.start_time)
        shifts: list[Shift] = []
        current_date = request.start_date.date()
        end_date = request.end_date.date()

        while current_date <= end_date:
            if request.days_of_week is None or current_date.weekday() in request.days_of_week:
                local_time = time(hour=hour, minute=minute, tzinfo=request.start_date.tzinfo)
                shift_start = normalize_utc(datetime.combine(current_date, local_time))
                shift_end = shift_start + timedelta(hours=template.duration_hours)
                shifts.append(self._shifts.save(_shift_from_template(template, shift_start, shift_end)))
            current_date += timedelta(days=1)

        return shifts

    def _get_owned_template(self, template_id: str, operator_id: str) -> ShiftTemplate:
        template = self._templates.get_template(template_id)
        if template is None or template.operator_id != operator_id:
            raise NotFoundError(f"Template not found: {template_id}")
        return template

    def _parse_start_time(self, value: str) -> tuple[int, int]:
        try:
            hour, minute = map(int, value.split(":"))
        except ValueError as exc:
            raise ValidationError("Invalid start_time format. Use HH:MM (e.g., '18:00')") from exc
        return hour, minute


def _shift_from_template(
    template: ShiftTemplate,
    start_time: datetime,
    end_time: datetime,
) -> Shift:
    return Shift(
        shift_id=str(uuid4()),
        operator_id=template.operator_id,
        role=template.role,
        location=template.location,
        start_time=start_time,
        end_time=end_time,
        pay_rate=template.pay_rate,
        notes=template.notes,
        status="open",
        created_at=utc_now(),
        workers_needed=template.workers_needed,
        workers_filled=0,
        account_id=template.account_id,
    )
