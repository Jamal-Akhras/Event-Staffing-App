from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import AccountModel
from apps.api.src.models.account import Account
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.services.notification_preferences import normalize_notification_preferences


class SqlAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, account_id: str) -> Account | None:
        row = self._session.get(AccountModel, account_id)
        return _to_domain(row) if row else None

    def save(self, account: Account) -> Account:
        row = self._session.get(AccountModel, account.account_id)
        if row is None:
            row = AccountModel()
            self._session.add(row)
        row.account_id = account.account_id
        row.name = account.name
        row.country = account.country
        row.currency = account.currency
        row.created_at = account.created_at
        row.venue_type = account.venue_type
        row.contact_email = account.contact_email
        row.contact_phone = account.contact_phone
        row.default_location = account.default_location
        row.avatar_url = account.avatar_url
        row.photos = list(account.photos)
        row.notification_preferences = dict(account.notification_preferences)
        self._session.commit()
        return _to_domain(row)


def _to_domain(row: AccountModel) -> Account:
    return Account(
        account_id=row.account_id,
        name=row.name,
        country=row.country,
        currency=row.currency,
        created_at=row.created_at,
        venue_type=getattr(row, "venue_type", None),
        contact_email=getattr(row, "contact_email", None),
        contact_phone=getattr(row, "contact_phone", None),
        default_location=getattr(row, "default_location", None),
        avatar_url=getattr(row, "avatar_url", None),
        photos=list(getattr(row, "photos", None) or []),
        notification_preferences=normalize_notification_preferences(getattr(row, "notification_preferences", None)),
    )
