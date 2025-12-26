from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import WorkerProfileModel
from apps.api.src.models.worker_profile import WorkerProfile


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
        self._session.commit()
        return profile


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
        pay_rate=model.pay_rate,
        notes=model.notes,
        updated_at=model.updated_at,
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
    model.pay_rate = profile.pay_rate
    model.notes = profile.notes
    model.updated_at = profile.updated_at
