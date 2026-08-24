from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.idempotency_models import IdempotencyRecordModel


class IdempotencyConflict(Exception):
    pass


@dataclass(frozen=True)
class IdempotencyStart:
    record_id: str | None
    cached_response: dict | None


class IdempotencyService:
    def __init__(self, session: Session | None) -> None:
        self._session = session

    def start(
        self,
        user_id: str,
        scope: str,
        key: str | None,
        payload: dict,
    ) -> IdempotencyStart:
        if key is None:
            return IdempotencyStart(None, None)
        digest = _request_hash(payload)
        if self._session is None:
            return _memory_start(user_id, scope, key, digest)
        row = self._find(user_id, scope, key)
        if row is not None and row.expires_at <= utc_now():
            self._session.delete(row)
            self._session.flush()
            row = None
        if row is None:
            row = IdempotencyRecordModel(
                record_id=str(uuid4()),
                user_id=user_id,
                scope=scope,
                key=key,
                request_hash=digest,
                response_payload=None,
                created_at=utc_now(),
                expires_at=utc_now() + timedelta(hours=24),
            )
            try:
                with self._session.begin_nested():
                    self._session.add(row)
                    self._session.flush()
            except IntegrityError:
                row = self._find(user_id, scope, key)
        if row is None:
            raise RuntimeError("Idempotency record could not be acquired.")
        if row.request_hash != digest:
            raise IdempotencyConflict("Idempotency-Key was already used with a different request.")
        return IdempotencyStart(row.record_id, row.response_payload)

    def finish(self, record_id: str | None, response: dict) -> None:
        if record_id is None:
            return
        if self._session is None:
            _MEMORY_RESPONSES[record_id] = response
            return
        row = self._session.get(IdempotencyRecordModel, record_id)
        if row is None:
            raise RuntimeError("Idempotency record disappeared before completion.")
        row.response_payload = response
        self._session.flush()

    def _find(self, user_id: str, scope: str, key: str):
        return (
            self._session.query(IdempotencyRecordModel)
            .filter_by(user_id=user_id, scope=scope, key=key)
            .with_for_update()
            .one_or_none()
        )


_MEMORY_KEYS: dict[tuple[str, str, str], tuple[str, str, datetime]] = {}
_MEMORY_RESPONSES: dict[str, dict] = {}


def _memory_start(user_id: str, scope: str, key: str, digest: str) -> IdempotencyStart:
    lookup = (user_id, scope, key)
    existing = _MEMORY_KEYS.get(lookup)
    now = utc_now()
    if existing is None or existing[2] <= now:
        record_id = str(uuid4())
        _MEMORY_KEYS[lookup] = (record_id, digest, now + timedelta(hours=24))
        return IdempotencyStart(record_id, None)
    record_id, prior_digest, _ = existing
    if prior_digest != digest:
        raise IdempotencyConflict("Idempotency-Key was already used with a different request.")
    return IdempotencyStart(record_id, _MEMORY_RESPONSES.get(record_id))


def _request_hash(payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def clear_in_memory_idempotency() -> None:
    _MEMORY_KEYS.clear()
    _MEMORY_RESPONSES.clear()
