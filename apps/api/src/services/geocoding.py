from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

_MIN_INTERVAL_SECONDS = 1.0

_cache: dict[str, tuple[float, float] | None] = {}
_lock = threading.Lock()
_last_request_at: float = 0.0


def geocode(location: str) -> tuple[float, float] | tuple[None, None]:
    """Return (lat, lng) for a location string, best-effort.

    Uses an in-memory cache and a 1 req/sec rate limit. To avoid blocking the
    request thread, this never sleeps and never queues behind another in-flight
    request: if the lock is held or the rate-limit window has not elapsed, it
    returns (None, None) without caching so a later call can retry.
    """
    key = location.strip().lower()

    cached = _cache.get(key, ...)
    if cached is not ...:
        return cached or (None, None)

    if not _lock.acquire(blocking=False):
        return (None, None)
    try:
        cached = _cache.get(key, ...)
        if cached is not ...:
            return cached or (None, None)

        global _last_request_at
        if time.monotonic() - _last_request_at < _MIN_INTERVAL_SECONDS:
            return (None, None)

        result = _fetch(location)
        _cache[key] = result
        _last_request_at = time.monotonic()
    finally:
        _lock.release()

    return result or (None, None)


def _fetch(location: str) -> tuple[float, float] | None:
    query = urllib.parse.urlencode({"q": location, "format": "json", "limit": "1"})
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "EventStaffingApp/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            results = json.loads(resp.read())
    except Exception:
        log.warning("geocoding lookup failed for %r", location, exc_info=True)
        return None
    if results:
        return float(results[0]["lat"]), float(results[0]["lon"])
    return None
