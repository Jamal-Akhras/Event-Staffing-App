from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from apps.api.src.datetime_utils import utc_now

log = logging.getLogger(__name__)


def run_no_show_sweep() -> None:
    from apps.api.src.db.database import SessionLocal
    from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
    from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
    from apps.api.src.repositories.sqlalchemy_worker_profile_repository import SqlAlchemyWorkerProfileRepository
    from apps.api.src.schemas import BookingTransitionRequest
    from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
    from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher

    session = SessionLocal()
    try:
        service = BookingLifecycleService(
            SqlAlchemyBookingRepository(session),
            SqlAlchemyWorkerProfileRepository(session),
            SqlAlchemyShiftRepository(session),
            SqlAlchemyOutboxPublisher(session),
        )
        updated = service.sweep_no_shows(BookingTransitionRequest(now=utc_now()))
        session.commit()
        if updated:
            log.info("no-show sweep: %d booking(s) marked", len(updated))
    except Exception:
        session.rollback()
        log.exception("no-show sweep failed")
    finally:
        session.close()


def run_recurring_generation() -> None:
    from apps.api.src.db.database import SessionLocal
    from apps.api.src.db.models import RecurringScheduleModel
    from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
    from apps.api.src.repositories.sqlalchemy_template_repository import SqlAlchemyTemplateRepository
    from apps.api.src.schemas import GenerateShiftsRequest
    from apps.api.src.services.template_service import TemplateService

    session = SessionLocal()
    try:
        now = utc_now()
        lookahead = now + timedelta(days=14)

        schedules = (
            session.query(RecurringScheduleModel)
            .filter(RecurringScheduleModel.is_active == True)
            .filter(RecurringScheduleModel.start_date <= lookahead)
            .filter(
                (RecurringScheduleModel.end_date == None) |
                (RecurringScheduleModel.end_date >= now)
            )
            .all()
        )

        service = TemplateService(
            SqlAlchemyTemplateRepository(session),
            SqlAlchemyShiftRepository(session),
        )
        total = 0
        for schedule in schedules:
            gen_from = schedule.last_generated_at or schedule.start_date or now
            if gen_from < now:
                gen_from = now
            if gen_from > lookahead:
                continue
            days_of_week = None
            if schedule.frequency == "weekly" and schedule.day_of_week is not None:
                days_of_week = [schedule.day_of_week]
            try:
                shifts = service.generate_shifts(
                    schedule.template_id,
                    GenerateShiftsRequest(
                        start_date=gen_from,
                        end_date=lookahead,
                        start_time=schedule.time_of_day,
                        days_of_week=days_of_week,
                    ),
                    schedule.operator_id,
                )
                total += len(shifts)
                schedule.last_generated_at = lookahead + timedelta(days=1)
                session.commit()
            except Exception:
                session.rollback()
                log.exception("recurring gen failed for schedule %s", schedule.schedule_id)

        if total:
            log.info("recurring generation: %d shift(s) created", total)
    except Exception:
        log.exception("recurring generation job failed")
    finally:
        session.close()


def create_scheduler() -> BackgroundScheduler:
    from apps.api.src.jobs.run_outbox_dispatch import run_outbox_dispatch

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_outbox_dispatch,
        "interval",
        seconds=5,
        id="outbox_dispatch",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(run_no_show_sweep, "interval", minutes=15, id="no_show_sweep", replace_existing=True)
    scheduler.add_job(run_recurring_generation, "cron", hour=3, minute=0, id="recurring_gen", replace_existing=True)
    return scheduler
