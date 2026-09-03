from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.booking_charge_adjustment import BookingChargeAdjustment
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_booking_repo,
    shared_booking_charge_adjustment_repository,
    shared_booking_charge_repository,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

VENUE_ID = "venue-1"
NOW = datetime(2030, 3, 25, 9, 0, tzinfo=UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}

GOLDEN = (
    "worker_id,worker_name,relationship,role,date,start,end,hours,hours_source,"
    "rate,wages,adjustment_ref,currency,booking_id\n"
    "w-temp,'=SUM(A1:A9),one_off,Bartender,2030-03-30,21:00,04:00,6.00,scheduled,"
    "14.50,87.00,,GBP,bk-csv-1\n"
    "w-pool,Poppy Pool,pool,Server,2030-03-31,18:00,23:00,5.00,clocked,"
    "16.00,80.00,,GBP,bk-csv-2\n"
    "w-pool,Poppy Pool,pool,Server,2030-03-31,,,0.50,correction,"
    "16.00,8.00,adj-1,GBP,bk-csv-2\n"
)


@pytest.fixture(autouse=True)
def clear_state():
    shared_booking_charge_repository().clear()
    shared_booking_charge_adjustment_repository().clear()
    yield
    shared_booking_charge_repository().clear()
    shared_booking_charge_adjustment_repository().clear()


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id=VENUE_ID, name="The Grapes", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb",
        )
    )
    return TestClient(main.app)


def _charge(
    charge_id: str, booking_id: str, worker_id: str, worker_name: str, relationship: str,
    role: str, start: datetime, end: datetime, hours: str, rate: str, wages: str,
) -> BookingCharge:
    return BookingCharge(
        charge_id=charge_id,
        booking_id=booking_id,
        shift_id=f"shift-{charge_id}",
        account_id=VENUE_ID,
        worker_id=worker_id,
        worker_name=worker_name,
        role=role,
        period="2030-03",
        start_time=start,
        end_time=end,
        completed_at=end,
        hours=Decimal(hours),
        pay_rate=Decimal(rate),
        wages=Decimal(wages),
        fee_percent=Decimal("0.00"),
        fee=Decimal("0.00"),
        total=Decimal(wages),
        currency="GBP",
        fee_waived=False,
        waiver_code=None,
        recorded_at=end,
        worker_relationship=relationship,
    )


def test_the_weekly_csv_matches_the_golden_file_across_the_dst_switch(client, in_memory_repos):
    charges = shared_booking_charge_repository()
    charges.record(
        _charge(
            "c1", "bk-csv-1", "w-temp", "=SUM(A1:A9)", "one_off", "Bartender",
            datetime(2030, 3, 30, 21, 0, tzinfo=UTC),
            datetime(2030, 3, 31, 3, 0, tzinfo=UTC),
            "6.00", "14.50", "87.00",
        )
    )
    charges.record(
        _charge(
            "c2", "bk-csv-2", "w-pool", "Poppy Pool", "pool", "Server",
            datetime(2030, 3, 31, 17, 0, tzinfo=UTC),
            datetime(2030, 3, 31, 22, 0, tzinfo=UTC),
            "5.00", "16.00", "80.00",
        )
    )
    in_memory_repos[get_booking_repo].save(
        Booking(
            booking_id="bk-csv-2",
            shift_id="shift-c2",
            worker_id="w-pool",
            operator_id="operator-1",
            start_time=datetime(2030, 3, 31, 17, 0, tzinfo=UTC),
            end_time=datetime(2030, 3, 31, 22, 0, tzinfo=UTC),
            state=BookingState.APPROVED,
            created_at=NOW,
            confirmed_at=NOW,
            checked_in_at=datetime(2030, 3, 31, 17, 0, tzinfo=UTC),
            checked_out_at=datetime(2030, 3, 31, 22, 0, tzinfo=UTC),
        )
    )
    shared_booking_charge_adjustment_repository().record(
        BookingChargeAdjustment(
            adjustment_id="adj-1",
            charge_id="c2",
            booking_id="bk-csv-2",
            delta_hours=Decimal("0.50"),
            delta_wages=Decimal("8.00"),
            delta_fee=Decimal("0.00"),
            reason="Stayed for close-down",
            created_by_user_id="operator-1",
            created_at=NOW,
        )
    )

    response = client.get(
        "/venues/me/timesheet.csv", params={"week_start": "2030-03-25"}, headers=OPERATOR
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text == GOLDEN
