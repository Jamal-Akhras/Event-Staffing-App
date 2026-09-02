from __future__ import annotations

import threading
from datetime import date

from apps.api.src.models.rota_publication import RotaPublication


class DuplicateRevisionError(Exception):
    pass


class InMemoryRotaPublicationRepository:
    def __init__(self) -> None:
        self._publications: list[RotaPublication] = []
        self._lock = threading.Lock()

    def save(self, publication: RotaPublication) -> RotaPublication:
        with self._lock:
            for existing in self._publications:
                if (
                    existing.venue_id == publication.venue_id
                    and existing.week_start == publication.week_start
                    and existing.revision == publication.revision
                ):
                    raise DuplicateRevisionError(
                        f"Revision {publication.revision} already exists for that week."
                    )
            self._publications.append(publication)
            return publication

    def latest_for_week(self, venue_id: str, week_start: date) -> RotaPublication | None:
        revisions = self.list_for_week(venue_id, week_start)
        return revisions[-1] if revisions else None

    def list_for_week(self, venue_id: str, week_start: date) -> list[RotaPublication]:
        return sorted(
            (
                publication
                for publication in self._publications
                if publication.venue_id == venue_id and publication.week_start == week_start
            ),
            key=lambda publication: publication.revision,
        )

    def clear(self) -> None:
        self._publications.clear()
