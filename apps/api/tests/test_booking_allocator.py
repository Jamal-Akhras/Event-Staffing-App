from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.booking_allocator import (
    OverlappingBookingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.sqlalchemy_booking_allocator import SqlAlchemyBookingAllocator
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from packages.domain.src.booking_state import BookingState

NOW = datetime(2030, 6, 1, 9, 0, tzinfo=UTC)
START = NOW + timedelta(days=7)


def _shift(shift_id: str = "shift-1", workers_needed: int = 1, start=START, hours: int = 5) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        role="Bartender",
        location="Main bar",
        start_time=start,
        end_time=start + timedelta(hours=hours),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="open",
        created_at=NOW,
        workers_needed=workers_needed,
        workers_filled=0,
    )


@pytest.fixture(params=["memory", "database"])
def world(request, repo_session):
    if request.param == "memory":
        bookings = InMemoryBookingRepository()
        shifts = InMemoryShiftRepository(bookings)
        bookings.attach_shift_repo(shifts)
        return {
            "bookings": bookings,
            "shifts": shifts,
            "allocator": InMemoryBookingAllocator(bookings, shifts),
        }
    return {
        "bookings": SqlAlchemyBookingRepository(repo_session),
        "shifts": SqlAlchemyShiftRepository(repo_session),
        "allocator": SqlAlchemyBookingAllocator(repo_session),
    }


def test_allocation_books_and_fills_the_shift(world):
    world["shifts"].save(_shift())
    allocated = world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1", attendance_mode="employed")

    assert allocated.booking.state == BookingState.CONFIRMED
    assert allocated.booking.attendance_mode == "employed"
    assert (allocated.shift.workers_filled, allocated.shift.status) == (1, "filled")


def test_a_full_shift_refuses_allocation(world):
    world["shifts"].save(_shift())
    world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1")
    with pytest.raises(ShiftFullError):
        world["allocator"].allocate("shift-1", "worker-2", NOW, "bk-2")


def test_a_worker_cannot_be_booked_twice_even_after_cancelling(world):
    world["shifts"].save(_shift(workers_needed=2))
    first = world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1")
    cancelled = first.booking.transition_to(BookingState.CANCELLED_BY_WORKER, NOW + timedelta(hours=1))
    world["bookings"].save(cancelled)

    with pytest.raises(WorkerAlreadyBookedError):
        world["allocator"].allocate("shift-1", "worker-1", NOW + timedelta(hours=2), "bk-2")


def test_overlapping_shifts_cannot_both_be_booked(world):
    world["shifts"].save(_shift("shift-1"))
    world["shifts"].save(_shift("shift-2", start=START + timedelta(hours=2)))
    world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1")

    with pytest.raises(OverlappingBookingError):
        world["allocator"].allocate("shift-2", "worker-1", NOW, "bk-2")


def test_non_overlapping_shifts_are_fine(world):
    world["shifts"].save(_shift("shift-1"))
    world["shifts"].save(_shift("shift-2", start=START + timedelta(hours=6)))
    world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1")
    allocated = world["allocator"].allocate("shift-2", "worker-1", NOW, "bk-2")
    assert allocated.booking.shift_id == "shift-2"


def test_a_cancelled_booking_does_not_block_a_different_shift(world):
    world["shifts"].save(_shift("shift-1"))
    world["shifts"].save(_shift("shift-2", start=START + timedelta(hours=2)))
    first = world["allocator"].allocate("shift-1", "worker-1", NOW, "bk-1")
    world["bookings"].save(
        first.booking.transition_to(BookingState.CANCELLED_BY_WORKER, NOW + timedelta(hours=1))
    )

    allocated = world["allocator"].allocate("shift-2", "worker-1", NOW + timedelta(hours=2), "bk-2")
    assert allocated.booking.shift_id == "shift-2"
