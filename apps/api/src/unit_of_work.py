from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


class RequestUnitOfWork:
    def __init__(self, session: Session | None) -> None:
        self.session = session
        self._after_commit: list[Callable[[], None]] = []
        self._after_rollback: list[Callable[[], None]] = []

    def after_commit(self, callback: Callable[[], None]) -> None:
        self._after_commit.append(callback)

    def after_rollback(self, callback: Callable[[], None]) -> None:
        self._after_rollback.append(callback)

    def commit(self) -> None:
        if self.session is not None:
            self.session.commit()
        self._after_rollback = []
        callbacks = self._after_commit
        self._after_commit = []
        self._run_callbacks(callbacks, "after-commit")

    def rollback(self) -> None:
        self._after_commit = []
        callbacks = self._after_rollback
        self._after_rollback = []
        try:
            if self.session is not None:
                self.session.rollback()
        finally:
            self._run_callbacks(callbacks, "after-rollback")

    def close(self) -> None:
        if self.session is not None:
            self.session.close()

    @staticmethod
    def _run_callbacks(callbacks: list[Callable[[], None]], stage: str) -> None:
        for callback in callbacks:
            try:
                callback()
            except Exception:
                log.exception("best-effort %s callback failed", stage)
