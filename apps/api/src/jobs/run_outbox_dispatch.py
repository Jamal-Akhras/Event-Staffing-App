from __future__ import annotations

import logging
import os
import socket

from apps.api.src.db.database import SessionLocal
from apps.api.src.services.outbox_dispatcher import dispatch_outbox_once
from apps.api.src.services.health import record_worker_heartbeat

log = logging.getLogger(__name__)
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def run_outbox_dispatch() -> None:
    stats = dispatch_outbox_once(SessionLocal, WORKER_ID)
    record_worker_heartbeat()
    if stats.events_fanned_out or stats.deliveries_sent or stats.deliveries_failed:
        log.info(
            "outbox cycle: events=%d delivered=%d failed=%d",
            stats.events_fanned_out,
            stats.deliveries_sent,
            stats.deliveries_failed,
        )
