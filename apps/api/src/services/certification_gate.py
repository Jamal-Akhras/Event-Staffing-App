from __future__ import annotations

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_certification import normalize_certification_name
from apps.api.src.repositories.worker_certification_repository import (
    WorkerCertificationRepository,
)
from apps.api.src.services.errors import ValidationError


class MissingCertificationError(ValidationError):
    def __init__(self, required: str) -> None:
        self.required = required
        super().__init__(
            f"This shift requires a current {required} certification at its start time."
        )


class CertificationGate:
    def __init__(self, certifications: WorkerCertificationRepository) -> None:
        self._certifications = certifications

    def ensure_certified(self, worker_id: str, shift: Shift) -> None:
        required = shift.required_certification
        if not required:
            return
        held = self._certifications.get(worker_id, normalize_certification_name(required))
        if held is None or held.expires_at <= shift.start_time:
            raise MissingCertificationError(required)
