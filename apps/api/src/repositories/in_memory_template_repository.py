from __future__ import annotations

from apps.api.src.models.shift_template import RecurringSchedule, ShiftTemplate


class InMemoryTemplateRepository:
    def __init__(self) -> None:
        self._templates: dict[str, ShiftTemplate] = {}
        self._schedules: dict[str, RecurringSchedule] = {}

    def get_template(self, template_id: str) -> ShiftTemplate | None:
        return self._templates.get(template_id)

    def save_template(self, template: ShiftTemplate) -> ShiftTemplate:
        self._templates[template.template_id] = template
        return template

    def list_templates(self, operator_id: str) -> list[ShiftTemplate]:
        items = [
            template
            for template in self._templates.values()
            if template.operator_id == operator_id
        ]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete_template(self, template_id: str) -> bool:
        if template_id not in self._templates:
            return False
        del self._templates[template_id]
        return True

    def get_schedule(self, schedule_id: str) -> RecurringSchedule | None:
        return self._schedules.get(schedule_id)

    def save_schedule(self, schedule: RecurringSchedule) -> RecurringSchedule:
        self._schedules[schedule.schedule_id] = schedule
        return schedule

    def list_schedules(self, operator_id: str) -> list[RecurringSchedule]:
        items = [
            schedule
            for schedule in self._schedules.values()
            if schedule.operator_id == operator_id
        ]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def list_active_schedules(self) -> list[RecurringSchedule]:
        return [
            schedule
            for schedule in self._schedules.values()
            if schedule.is_active
        ]

    def delete_schedule(self, schedule_id: str) -> bool:
        if schedule_id not in self._schedules:
            return False
        del self._schedules[schedule_id]
        return True

    def clear(self) -> None:
        self._templates.clear()
        self._schedules.clear()
