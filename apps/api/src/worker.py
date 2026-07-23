from __future__ import annotations

import logging
import signal
from threading import Event
from types import FrameType

from apps.api.src.observability import init_sentry
from apps.api.src.scheduler import create_scheduler

log = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_sentry()
    stop_event = Event()

    def request_stop(signum: int, frame: FrameType | None) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    scheduler = create_scheduler()
    scheduler.start()
    log.info("scheduler worker started")
    try:
        stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        log.info("scheduler worker stopped")


if __name__ == "__main__":
    main()
