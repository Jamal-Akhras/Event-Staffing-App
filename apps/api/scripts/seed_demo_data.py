from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.src.db.database import Base, SessionLocal, engine
from apps.api.src.db.models import (
    ApplicationMessageHistoryModel,
    ApplicationModel,
    BookingModel,
    MessageModel,
    RecurringScheduleModel,
    ShiftModel,
    ShiftTemplateModel,
    WorkerProfileModel,
)
from apps.api.src.db.tenancy_models import VenueModel
from packages.domain.src.booking_state import BookingState


OPERATOR_ID = "venue-default"
VENUE_ID = "demo-venue-account"
DEMO_WORKER_ID = "demo-worker-profile"
WORKERS = ["worker-1", "worker-2", "worker-3", "worker-4"]
SHIFT_IDS = [
    "demo-shift-checkin",
    "demo-shift-open-bar",
    "demo-shift-open-floor",
    "demo-shift-filled",
    "demo-shift-paid",
    "demo-shift-pending-pay",
]
APPLICATION_IDS = [
    "demo-app-checkin",
    "demo-app-worker-2-bar",
    "demo-app-worker-3-bar",
    "demo-app-worker-4-floor",
    "demo-app-rejected",
    "demo-app-waiting-bar",
    "demo-app-waiting-floor",
    "demo-app-paid",
    "demo-app-pending-pay",
]
BOOKING_IDS = [
    "demo-booking-checkin",
    "demo-booking-filled",
    "demo-booking-paid",
    "demo-booking-pending-pay",
]
TEMPLATE_IDS = ["demo-template-bar", "demo-template-floor"]
MESSAGE_IDS = [
    "demo-message-app-1",
    "demo-message-app-2",
    "demo-message-booking-1",
    "demo-message-booking-2",
]
HISTORY_IDS = ["demo-history-1"]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    now = datetime.now(UTC).replace(microsecond=0)
    with SessionLocal() as session:
        require_demo_venue(session)
        delete_demo_data(session)
        seed_workers(session, now)
        seed_shifts(session, now)
        session.flush()
        seed_bookings(session, now)
        session.flush()
        seed_applications(session, now)
        session.flush()
        seed_templates(session, now)
        seed_messages(session, now)
        session.commit()
    print(f"Seeded demo data for venue {VENUE_ID} and worker-1.")


def require_demo_venue(session) -> None:
    if session.get(VenueModel, VENUE_ID) is None:
        raise RuntimeError(
            f"Venue {VENUE_ID} is missing. Run apps.api.scripts.prepare_demo_accounts first "
            "so demo shifts belong to the demo venue."
        )


def delete_demo_data(session) -> None:
    session.query(ApplicationMessageHistoryModel).filter(
        ApplicationMessageHistoryModel.history_id.in_(HISTORY_IDS)
    ).delete(synchronize_session=False)
    session.query(MessageModel).filter(MessageModel.message_id.in_(MESSAGE_IDS)).delete(
        synchronize_session=False
    )
    session.query(ApplicationModel).filter(
        ApplicationModel.application_id.in_(APPLICATION_IDS)
    ).delete(synchronize_session=False)
    session.query(BookingModel).filter(BookingModel.booking_id.in_(BOOKING_IDS)).delete(
        synchronize_session=False
    )
    session.query(RecurringScheduleModel).filter(
        RecurringScheduleModel.operator_id == OPERATOR_ID
    ).delete(synchronize_session=False)
    session.query(ShiftTemplateModel).filter(
        ShiftTemplateModel.template_id.in_(TEMPLATE_IDS)
    ).delete(synchronize_session=False)
    session.query(ShiftModel).filter(ShiftModel.shift_id.in_(SHIFT_IDS)).delete(
        synchronize_session=False
    )
    session.query(WorkerProfileModel).filter(
        WorkerProfileModel.worker_id.in_(WORKERS)
    ).delete(synchronize_session=False)
    session.flush()


def seed_workers(session, now: datetime) -> None:
    workers = [
        ("worker-1", "Maya Carter", "Bartender", "Downtown", 5, 0.96, ["Top rated", "Mixology"]),
        ("worker-2", "Andre Lewis", "Server", "Uptown", 3, 0.88, ["Reliable"]),
        ("worker-3", "Priya Shah", "Host", "Midtown", 2, 0.81, ["Fast response"]),
        ("worker-4", "Leo Grant", "Barback", "Downtown", 1, 0.74, ["New"]),
    ]
    for worker_id, name, role, city, years, score, badges in workers:
        session.add(WorkerProfileModel(
            worker_id=worker_id,
            display_name=name,
            role=role,
            city=city,
            experience_years=years,
            reliability_score=score,
            badges=badges,
            bio=f"{role} available for events and late service windows.",
            languages=["English", "Spanish"] if worker_id == "worker-1" else ["English"],
            email=f"{worker_id}@example.com",
            phone="555-0100",
            address="123 Demo Street",
            emergency_contact="Demo Contact 555-0199",
            pay_rate=28.0 + years,
            notes="Seeded POC worker profile.",
            updated_at=now,
        ))


def seed_shifts(session, now: datetime) -> None:
    shifts = [
        ("demo-shift-checkin", "Bartender", "Harbor Hall - Main Bar", now + timedelta(minutes=10), 4, 32, "filled", 1, 1),
        ("demo-shift-open-bar", "Bartender", "Harbor Hall - Rooftop", now + timedelta(days=1, hours=2), 6, 34, "open", 2, 0),
        ("demo-shift-open-floor", "Server", "Pearl Room - Banquet", next_saturday(now), 5, 26, "open", 4, 1),
        ("demo-shift-filled", "Host", "Lumen Lounge", now + timedelta(days=2), 4, 24, "filled", 1, 1),
        ("demo-shift-paid", "Bartender", "Harbor Hall - Patio", now - timedelta(days=2), 6, 31, "filled", 1, 1),
        ("demo-shift-pending-pay", "Server", "Pearl Room - Gala", now - timedelta(days=1), 5, 27, "filled", 1, 1),
    ]
    for shift_id, role, location, start, hours, pay, status, needed, filled in shifts:
        session.add(ShiftModel(
            shift_id=shift_id,
            operator_id=OPERATOR_ID,
            venue_id=VENUE_ID,
            role=role,
            location=location,
            start_time=start,
            end_time=start + timedelta(hours=hours),
            pay_rate=pay,
            notes="Black attire. Check in with the floor lead 15 minutes early.",
            status=status,
            created_at=now - timedelta(hours=3),
            workers_needed=needed,
            workers_filled=filled,
        ))


def seed_applications(session, now: datetime) -> None:
    rows = [
        ("demo-app-checkin", "demo-shift-checkin", DEMO_WORKER_ID, "approved", "demo-booking-checkin", now - timedelta(hours=2)),
        ("demo-app-worker-2-bar", "demo-shift-open-bar", "worker-2", "applied", None, None),
        ("demo-app-worker-3-bar", "demo-shift-open-bar", "worker-3", "applied", None, None),
        ("demo-app-worker-4-floor", "demo-shift-open-floor", "worker-4", "applied", None, None),
        ("demo-app-rejected", "demo-shift-open-floor", "worker-3", "rejected", None, now - timedelta(hours=1)),
        ("demo-app-waiting-bar", "demo-shift-open-bar", DEMO_WORKER_ID, "applied", None, None),
        ("demo-app-waiting-floor", "demo-shift-open-floor", DEMO_WORKER_ID, "applied", None, None),
        ("demo-app-paid", "demo-shift-paid", DEMO_WORKER_ID, "approved", "demo-booking-paid", now - timedelta(days=2)),
        ("demo-app-pending-pay", "demo-shift-pending-pay", DEMO_WORKER_ID, "approved", "demo-booking-pending-pay", now - timedelta(days=1)),
    ]
    shifts = {shift.shift_id: shift for shift in session.query(ShiftModel).all()}
    for app_id, shift_id, worker_id, status, booking_id, decided_at in rows:
        shift = shifts[shift_id]
        created_at = decided_at - timedelta(hours=2) if decided_at else now - timedelta(hours=4)
        session.add(ApplicationModel(
            application_id=app_id,
            shift_id=shift_id,
            worker_id=worker_id,
            operator_id=OPERATOR_ID,
            start_time=shift.start_time,
            end_time=shift.end_time,
            status=status,
            message=f"I can cover {shift.role.lower()} for this service.",
            booking_id=booking_id,
            created_at=created_at,
            decided_at=decided_at,
        ))


def seed_bookings(session, now: datetime) -> None:
    shifts = {shift.shift_id: shift for shift in session.query(ShiftModel).all()}
    rows = [
        ("demo-booking-checkin", "demo-shift-checkin", DEMO_WORKER_ID, BookingState.CONFIRMED, now - timedelta(hours=2), None, None, None),
        ("demo-booking-filled", "demo-shift-filled", "worker-2", BookingState.CONFIRMED, now - timedelta(hours=1), None, None, None),
        ("demo-booking-paid", "demo-shift-paid", DEMO_WORKER_ID, BookingState.PAID, now - timedelta(days=3), now - timedelta(days=2, minutes=5), now - timedelta(days=2) + timedelta(hours=6, minutes=5), now - timedelta(days=1)),
        ("demo-booking-pending-pay", "demo-shift-pending-pay", DEMO_WORKER_ID, BookingState.APPROVED, now - timedelta(days=2), now - timedelta(days=1, minutes=5), now - timedelta(days=1) + timedelta(hours=5, minutes=5), None),
    ]
    for booking_id, shift_id, worker_id, state, created_at, checked_in_at, checked_out_at, paid_at in rows:
        shift = shifts[shift_id]
        session.add(BookingModel(
            booking_id=booking_id,
            shift_id=shift_id,
            worker_id=worker_id,
            operator_id=OPERATOR_ID,
            start_time=shift.start_time,
            end_time=shift.end_time,
            state=state,
            created_at=created_at,
            confirmed_at=created_at,
            checked_in_at=checked_in_at,
            checked_out_at=checked_out_at,
            approved_at=checked_out_at,
            paid_at=paid_at,
            cancelled_at=None,
            no_show_at=None,
        ))


def seed_templates(session, now: datetime) -> None:
    for template_id, name, role, location, hours, rate, needed in [
        ("demo-template-bar", "Friday Rooftop Bar", "Bartender", "Harbor Hall - Rooftop", 6, 34, 2),
        ("demo-template-floor", "Banquet Dinner Floor", "Server", "Pearl Room - Banquet", 5, 26, 4),
    ]:
        session.add(ShiftTemplateModel(
            template_id=template_id,
            operator_id=OPERATOR_ID,
            venue_id=VENUE_ID,
            name=name,
            role=role,
            location=location,
            duration_hours=hours,
            pay_rate=rate,
            workers_needed=needed,
            notes="Seeded repeatable POC template.",
            created_at=now,
            updated_at=now,
        ))


def seed_messages(session, now: datetime) -> None:
    session.add_all([
        MessageModel(message_id="demo-message-app-1", shift_id="demo-shift-open-bar", application_id="demo-app-worker-2-bar", booking_id=None, sender_id="worker-2", sender_role="worker", content="I have worked rooftop service and can bring my bar kit.", read_at=None, created_at=now - timedelta(hours=2)),
        MessageModel(message_id="demo-message-app-2", shift_id="demo-shift-open-bar", application_id="demo-app-worker-2-bar", booking_id=None, sender_id=OPERATOR_ID, sender_role="operator", content="Thanks. Can you arrive 20 minutes early for setup?", read_at=None, created_at=now - timedelta(hours=1, minutes=30)),
        MessageModel(message_id="demo-message-booking-1", shift_id="demo-shift-checkin", application_id=None, booking_id="demo-booking-checkin", sender_id=OPERATOR_ID, sender_role="operator", content="Use the staff entrance on 3rd Street.", read_at=None, created_at=now - timedelta(minutes=45)),
        MessageModel(message_id="demo-message-booking-2", shift_id="demo-shift-checkin", application_id=None, booking_id="demo-booking-checkin", sender_id="worker-1", sender_role="worker", content="Got it. I am nearby and ready to check in.", read_at=None, created_at=now - timedelta(minutes=20)),
        ApplicationMessageHistoryModel(history_id="demo-history-1", application_id="demo-app-worker-2-bar", message="Original shorter application note.", edited_at=now - timedelta(hours=3)),
    ])


def next_saturday(now: datetime) -> datetime:
    days_ahead = (5 - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target = now + timedelta(days=days_ahead)
    return target.replace(hour=17, minute=0, second=0, microsecond=0)


if __name__ == "__main__":
    main()
