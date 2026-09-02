from __future__ import annotations

from datetime import date
from typing import Protocol

from apps.api.src.models.rota_publication import RotaPublication


class RotaPublicationRepository(Protocol):
    def save(self, publication: RotaPublication) -> RotaPublication: ...

    def latest_for_week(self, venue_id: str, week_start: date) -> RotaPublication | None: ...

    def list_for_week(self, venue_id: str, week_start: date) -> list[RotaPublication]: ...
