from __future__ import annotations

import argparse
from datetime import UTC, date, datetime

from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_partner_code_repository import SqlAlchemyPartnerCodeRepository
from apps.api.src.services.billing_service import new_partner_code


def end_of_day(value: str) -> datetime:
    day = date.fromisoformat(value)
    return datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=UTC)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a founding-partner code that waives the platform fee.")
    parser.add_argument("--label", required=True, help='Who it is for, e.g. "Bath founding ten"')
    parser.add_argument("--max-redemptions", type=int, default=1, help="How many venues may use this code")
    parser.add_argument("--expires", help="Last day the code can be redeemed, YYYY-MM-DD")
    parser.add_argument("--prefix", default="BATH")
    parser.add_argument("--created-by", default="founder")
    args = parser.parse_args()

    code = new_partner_code(
        prefix=args.prefix,
        label=args.label,
        max_redemptions=args.max_redemptions,
        created_by=args.created_by,
        now=datetime.now(UTC).replace(microsecond=0),
        expires_at=end_of_day(args.expires) if args.expires else None,
    )
    with SessionLocal() as session:
        SqlAlchemyPartnerCodeRepository(session).save_code(code)
        session.commit()

    print(f"Code:          {code.code}")
    print(f"Label:         {code.label}")
    print(f"Fee waiver:    {code.waiver_months} months from redemption or {code.shift_cap} completed shifts")
    print(f"Redemptions:   {code.max_redemptions}")
    if code.expires_at:
        print(f"Redeem by:     {code.expires_at:%d %b %Y}")


if __name__ == "__main__":
    main()
