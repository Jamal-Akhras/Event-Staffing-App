from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import ShiftTemplateModel, RecurringScheduleModel
from apps.api.src.money import money
from apps.api.src.models.shift_template import ShiftTemplate, RecurringSchedule


class SqlAlchemyTemplateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_template(self, template_id: str) -> ShiftTemplate | None:
        model = self._session.get(ShiftTemplateModel, template_id)
        if model is None:
            return None
        return _template_to_domain(model)

    def save_template(self, template: ShiftTemplate) -> ShiftTemplate:
        model = self._session.get(ShiftTemplateModel, template.template_id)
        if model is None:
            model = ShiftTemplateModel(template_id=template.template_id)
            self._session.add(model)
        _apply_template_domain(model, template)
        self._session.flush()
        return template

    def list_templates(self, operator_id: str) -> list[ShiftTemplate]:
        rows = (
            self._session.query(ShiftTemplateModel)
            .filter(ShiftTemplateModel.operator_id == operator_id)
            .order_by(desc(ShiftTemplateModel.created_at))
            .all()
        )
        return [_template_to_domain(row) for row in rows]

    def delete_template(self, template_id: str) -> bool:
        model = self._session.get(ShiftTemplateModel, template_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def get_schedule(self, schedule_id: str) -> RecurringSchedule | None:
        model = self._session.get(RecurringScheduleModel, schedule_id)
        if model is None:
            return None
        return _schedule_to_domain(model)

    def save_schedule(self, schedule: RecurringSchedule) -> RecurringSchedule:
        model = self._session.get(RecurringScheduleModel, schedule.schedule_id)
        if model is None:
            model = RecurringScheduleModel(schedule_id=schedule.schedule_id)
            self._session.add(model)
        _apply_schedule_domain(model, schedule)
        self._session.flush()
        return schedule

    def list_schedules(self, operator_id: str) -> list[RecurringSchedule]:
        rows = (
            self._session.query(RecurringScheduleModel)
            .filter(RecurringScheduleModel.operator_id == operator_id)
            .order_by(desc(RecurringScheduleModel.created_at))
            .all()
        )
        return [_schedule_to_domain(row) for row in rows]

    def list_active_schedules(self) -> list[RecurringSchedule]:
        rows = (
            self._session.query(RecurringScheduleModel)
            .filter(RecurringScheduleModel.is_active == True)
            .all()
        )
        return [_schedule_to_domain(row) for row in rows]

    def delete_schedule(self, schedule_id: str) -> bool:
        model = self._session.get(RecurringScheduleModel, schedule_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True


def _template_to_domain(model: ShiftTemplateModel) -> ShiftTemplate:
    return ShiftTemplate(
        template_id=model.template_id,
        operator_id=model.operator_id,
        name=model.name,
        role=model.role,
        location=model.location,
        duration_hours=model.duration_hours,
        pay_rate=money(model.pay_rate),
        workers_needed=model.workers_needed,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
        account_id=getattr(model, "account_id", None),
    )


def _apply_template_domain(model: ShiftTemplateModel, template: ShiftTemplate) -> None:
    model.operator_id = template.operator_id
    model.name = template.name
    model.role = template.role
    model.location = template.location
    model.duration_hours = template.duration_hours
    model.pay_rate = money(template.pay_rate)
    model.workers_needed = template.workers_needed
    model.notes = template.notes
    model.created_at = template.created_at
    model.updated_at = template.updated_at
    model.account_id = template.account_id


def _schedule_to_domain(model: RecurringScheduleModel) -> RecurringSchedule:
    return RecurringSchedule(
        schedule_id=model.schedule_id,
        template_id=model.template_id,
        operator_id=model.operator_id,
        frequency=model.frequency,
        day_of_week=model.day_of_week,
        time_of_day=model.time_of_day,
        start_date=model.start_date,
        end_date=model.end_date,
        is_active=model.is_active,
        created_at=model.created_at,
        last_generated_at=model.last_generated_at,
    )


def _apply_schedule_domain(model: RecurringScheduleModel, schedule: RecurringSchedule) -> None:
    model.template_id = schedule.template_id
    model.operator_id = schedule.operator_id
    model.frequency = schedule.frequency
    model.day_of_week = schedule.day_of_week
    model.time_of_day = schedule.time_of_day
    model.start_date = schedule.start_date
    model.end_date = schedule.end_date
    model.is_active = schedule.is_active
    model.created_at = schedule.created_at
    model.last_generated_at = schedule.last_generated_at
