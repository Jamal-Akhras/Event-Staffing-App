from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from apps.api.src.datetime_utils import utc_now

log = logging.getLogger(__name__)


def run_no_show_sweep() -> None:
    from apps.api.src.jobs.run_no_show_sweep import run

    try:
        updated = run()
        if updated:
            log.info("no-show sweep: %d booking(s) marked", updated)
    except Exception:
        log.exception("no-show sweep failed")


def run_escalation_sweep() -> None:
    from apps.api.src.jobs.run_escalation_sweep import run

    try:
        moved = run()
        if moved:
            log.info("escalation sweep: %d shift(s) moved", moved)
    except Exception:
        log.exception("escalation sweep failed")


def run_workforce_expiry_sweep() -> None:
    from apps.api.src.jobs.run_workforce_expiry_sweep import run

    try:
        expired = run()
        if expired:
            log.info("workforce expiry sweep: %d request(s) expired", expired)
    except Exception:
        log.exception("workforce expiry sweep failed")


def run_subscription_minting() -> None:
    from apps.api.src.jobs.run_subscription_minting import run

    try:
        minted = run()
        if minted:
            log.info("subscription minting: %d charge(s) created", minted)
    except Exception:
        log.exception("subscription minting failed")


def run_certification_expiry_sweep() -> None:
    from apps.api.src.jobs.run_certification_expiry_sweep import run

    try:
        published = run()
        if published:
            log.info("certification expiry sweep: %d notice(s) published", published)
    except Exception:
        log.exception("certification expiry sweep failed")


def run_auto_accept_sweep() -> None:
    from apps.api.src.jobs.run_auto_accept_sweep import run

    try:
        evaluated = run()
        if evaluated:
            log.info("auto-accept sweep: %d offer(s) evaluated", evaluated)
    except Exception:
        log.exception("auto-accept sweep failed")


def run_recurring_generation() -> None:
    from apps.api.src.db.database import SessionLocal
    from apps.api.src.db.models import RecurringScheduleModel
    from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
    from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
    from apps.api.src.repositories.sqlalchemy_template_repository import SqlAlchemyTemplateRepository
    from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
        SqlAlchemyWorkerRelationshipRepository,
    )
    from apps.api.src.services.escalation_service import EscalationService
    from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher
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

        shift_repository = SqlAlchemyShiftRepository(session)
        service = TemplateService(
            SqlAlchemyTemplateRepository(session),
            shift_repository,
            EscalationService(
                shift_repository,
                SqlAlchemyWorkerRelationshipRepository(session),
                SqlAlchemyAccountRepository(session),
                SqlAlchemyOutboxPublisher(session),
            ),
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
    scheduler.add_job(run_escalation_sweep, "interval", minutes=5, id="escalation_sweep", replace_existing=True)
    scheduler.add_job(run_workforce_expiry_sweep, "interval", minutes=10, id="workforce_expiry_sweep", replace_existing=True)
    scheduler.add_job(run_recurring_generation, "cron", hour=3, minute=0, id="recurring_gen", replace_existing=True)
    scheduler.add_job(run_certification_expiry_sweep, "cron", hour=7, minute=0, id="certification_expiry_sweep", replace_existing=True)
    scheduler.add_job(run_subscription_minting, "cron", day=1, hour=2, minute=0, id="subscription_minting", replace_existing=True)
    scheduler.add_job(
        run_auto_accept_sweep,
        "interval",
        minutes=1,
        id="auto_accept_sweep",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
