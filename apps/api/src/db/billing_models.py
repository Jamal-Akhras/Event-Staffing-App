from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class PartnerCodeModel(Base):
    __tablename__ = "partner_codes"
    __table_args__ = (
        CheckConstraint("waiver_months > 0", name="ck_partner_codes_waiver_months_positive"),
        CheckConstraint("shift_cap > 0", name="ck_partner_codes_shift_cap_positive"),
        CheckConstraint("max_redemptions > 0", name="ck_partner_codes_max_redemptions_positive"),
    )

    code = Column(String(32), primary_key=True)
    label = Column(String(160), nullable=False)
    waiver_months = Column(Integer, nullable=False)
    shift_cap = Column(Integer, nullable=False)
    max_redemptions = Column(Integer, nullable=False)
    created_at = Column(UtcDateTime, nullable=False)
    created_by = Column(String(120), nullable=False)
    expires_at = Column(UtcDateTime, nullable=True)


class PartnerCodeRedemptionModel(Base):
    __tablename__ = "partner_code_redemptions"
    __table_args__ = (
        UniqueConstraint("account_id", name="uq_partner_code_redemptions_account"),
        CheckConstraint("shift_cap > 0", name="ck_partner_code_redemptions_shift_cap_positive"),
    )

    redemption_id = Column(String, primary_key=True)
    code = Column(String(32), ForeignKey("partner_codes.code", ondelete="RESTRICT"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("venues.venue_id", ondelete="CASCADE"), nullable=False)
    redeemed_at = Column(UtcDateTime, nullable=False)
    redeemed_by_user_id = Column(String, nullable=False)
    fee_waived_until = Column(UtcDateTime, nullable=False)
    shift_cap = Column(Integer, nullable=False)
