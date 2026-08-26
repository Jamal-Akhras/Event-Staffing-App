from __future__ import annotations

from typing import Protocol

from apps.api.src.models.shift_template import ShiftTemplate, RecurringSchedule


class TemplateRepository(Protocol):
    def get_template(self, template_id: str) -> ShiftTemplate | None:
        ...

    def save_template(self, template: ShiftTemplate) -> ShiftTemplate:
        ...

    def list_templates(self, operator_id: str) -> list[ShiftTemplate]:
        ...

    def delete_template(self, template_id: str) -> bool:
        ...

    def get_schedule(self, schedule_id: str) -> RecurringSchedule | None:
        ...

    def save_schedule(self, schedule: RecurringSchedule) -> RecurringSchedule:
        ...

    def list_schedules(self, operator_id: str) -> list[RecurringSchedule]:
        ...


    def delete_schedule(self, schedule_id: str) -> bool:
        ...
