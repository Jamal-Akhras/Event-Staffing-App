from __future__ import annotations

import time
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select, text

from apps.api.src.config import get_redis_url, use_in_memory_backends, use_in_memory_repositories
from apps.api.src.datetime_utils import utc_now

_WORKER_HEARTBEAT_KEY = "worker:heartbeat:outbox"
_WORKER_STALE_SECONDS = 60


def record_worker_heartbeat() -> None:
    if use_in_memory_backends():
        return
    _redis_client().set(_WORKER_HEARTBEAT_KEY, str(time.time()), ex=180)


def readiness_snapshot() -> tuple[bool, dict[str, Any]]:
    components: dict[str, Any] = {}
    database_ready = _database_status(components)
    redis_ready = _redis_status(components)
    if database_ready and not use_in_memory_repositories():
        _outbox_status(components)
    if redis_ready and not use_in_memory_backends():
        _worker_status(components)
    return database_ready and redis_ready, components


def _database_status(components: dict[str, Any]) -> bool:
    if use_in_memory_repositories():
        components["database"] = "development_in_memory"
        return True
    try:
        from apps.api.src.db.database import engine

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        components["database"] = "ok"
        return True
    except Exception:
        components["database"] = "unavailable"
        return False


def _redis_status(components: dict[str, Any]) -> bool:
    if use_in_memory_backends():
        components["redis"] = "development_in_memory"
        return True
    try:
        _redis_client().ping()
        components["redis"] = "ok"
        return True
    except Exception:
        components["redis"] = "unavailable"
        return False


def _outbox_status(components: dict[str, Any]) -> None:
    from apps.api.src.db.database import SessionLocal
    from apps.api.src.db.notification_models import NotificationDeliveryModel, OutboxEventModel

    cutoff = utc_now() - timedelta(minutes=5)
    with SessionLocal() as session:
        stale_count = session.scalar(
            select(func.count())
            .select_from(OutboxEventModel)
            .where(OutboxEventModel.processed_at.is_(None))
            .where(OutboxEventModel.dead_lettered_at.is_(None))
            .where(OutboxEventModel.available_at < cutoff)
        )
        dead_letters = session.scalar(
            select(func.count())
            .select_from(NotificationDeliveryModel)
            .where(NotificationDeliveryModel.status == "dead_letter")
        )
    components["outbox"] = {
        "status": "degraded" if stale_count or dead_letters else "ok",
        "stale_events": int(stale_count or 0),
        "dead_letters": int(dead_letters or 0),
    }


def _worker_status(components: dict[str, Any]) -> None:
    value = _redis_client().get(_WORKER_HEARTBEAT_KEY)
    age = time.time() - float(value) if value else None
    components["worker"] = {
        "status": "ok" if age is not None and age <= _WORKER_STALE_SECONDS else "stale",
        "heartbeat_age_seconds": round(age, 1) if age is not None else None,
    }


def _redis_client():
    import redis

    return redis.Redis.from_url(get_redis_url(), decode_responses=True)
