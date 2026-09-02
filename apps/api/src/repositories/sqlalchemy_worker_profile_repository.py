from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel, ShiftModel, WorkerProfileModel
from apps.api.src.money import money
from apps.api.src.models.worker_profile import WorkerProfile
from packages.domain.src.booking_state import BookingState


class SqlAlchemyWorkerProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, worker_id: str) -> WorkerProfile | None:
        model = self._session.get(WorkerProfileModel, worker_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, profile: WorkerProfile) -> WorkerProfile:
        model = self._session.get(WorkerProfileModel, profile.worker_id)
        if model is None:
            model = WorkerProfileModel(worker_id=profile.worker_id)
            self._session.add(model)
        _apply_domain(model, profile)
        self._session.flush()
        return profile

    def list_all(self) -> list[WorkerProfile]:
        return [_to_domain(m) for m in self._session.query(WorkerProfileModel).all()]

    def list_by_ids(self, worker_ids: list[str]) -> list[WorkerProfile]:
        if not worker_ids:
            return []
        rows = (
            self._session.query(WorkerProfileModel)
            .filter(WorkerProfileModel.worker_id.in_(worker_ids))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_for_account(self, account_id: str) -> list[WorkerProfile]:
        completed_states = {BookingState.CHECKED_OUT, BookingState.PAID}


        worker_id_subq = (
            self._session.query(BookingModel.worker_id)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .filter(ShiftModel.account_id == account_id)
            .filter(BookingModel.state.in_(completed_states))
            .distinct()
            .subquery()
        )
        rows = (
            self._session.query(WorkerProfileModel)
            .filter(WorkerProfileModel.worker_id.in_(self._session.query(worker_id_subq)))
            .filter(WorkerProfileModel.allow_venue_recontact.is_(True))
            .all()
        )
        return [_to_domain(m) for m in rows]


def _to_domain(model: WorkerProfileModel) -> WorkerProfile:
    return WorkerProfile(
        worker_id=model.worker_id,
        display_name=model.display_name,
        role=model.role,
        city=model.city,
        experience_years=model.experience_years,
        reliability_score=model.reliability_score,
        badges=list(model.badges or []),
        bio=model.bio,
        languages=list(model.languages or []),
        email=model.email,
        phone=model.phone,
        address=model.address,
        emergency_contact=model.emergency_contact,
        pay_rate=money(model.pay_rate) if model.pay_rate is not None else None,
        notes=model.notes,
        updated_at=model.updated_at,
        avatar_url=getattr(model, "avatar_url", None),
        allow_venue_recontact=bool(getattr(model, "allow_venue_recontact", False)),
        market_id=model.market_id,
    )


def _apply_domain(model: WorkerProfileModel, profile: WorkerProfile) -> None:
    model.display_name = profile.display_name
    model.role = profile.role
    model.city = profile.city
    model.experience_years = profile.experience_years
    model.reliability_score = profile.reliability_score
    model.badges = list(profile.badges)
    model.bio = profile.bio
    model.languages = list(profile.languages)
    model.email = profile.email
    model.phone = profile.phone
    model.address = profile.address
    model.emergency_contact = profile.emergency_contact
    model.pay_rate = money(profile.pay_rate) if profile.pay_rate is not None else None
    model.notes = profile.notes
    model.updated_at = profile.updated_at
    model.avatar_url = profile.avatar_url
    model.allow_venue_recontact = profile.allow_venue_recontact
    model.market_id = profile.market_id
