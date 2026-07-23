from __future__ import annotations

from typing import Protocol

from apps.api.src.models.shift_template import ShiftTemplate, RecurringSchedule


class TemplateRepository(Protocol):
    def get_template(self, template_id: str) -> ShiftTemplate | None:
        raise NotImplementedError

    def save_template(self, template: ShiftTemplate) -> ShiftTemplate:
        raise NotImplementedError

    def list_templates(self, operator_id: str) -> list[ShiftTemplate]:
        raise NotImplementedError

    def delete_template(self, template_id: str) -> bool:
        raise NotImplementedError

    def get_schedule(self, schedule_id: str) -> RecurringSchedule | None:
        raise NotImplementedError

    def save_schedule(self, schedule: RecurringSchedule) -> RecurringSchedule:
        raise NotImplementedError

    def list_schedules(self, operator_id: str) -> list[RecurringSchedule]:
        raise NotImplementedError

    def list_active_schedules(self) -> list[RecurringSchedule]:
        raise NotImplementedError

    def delete_schedule(self, schedule_id: str) -> bool:
        raise NotImplementedError
