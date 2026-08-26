from __future__ import annotations

import logging
import threading

from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

log = logging.getLogger(__name__)

USER_AGENT = "EventStaffingApp/1.0"
MIN_INTERVAL_SECONDS = 1.0

_cache: dict[str, tuple[float, float] | None] = {}
_lock = threading.Lock()
_lookup = RateLimiter(
    Nominatim(user_agent=USER_AGENT, timeout=3).geocode,
    min_delay_seconds=MIN_INTERVAL_SECONDS,
    max_retries=0,
    swallow_exceptions=False,
)


def geocode(location: str) -> tuple[float, float] | tuple[None, None]:
    key = location.strip().lower()
    if key in _cache:
        return _cache[key] or (None, None)
    with _lock:
        if key in _cache:
            return _cache[key] or (None, None)
        result = _fetch(location)
        _cache[key] = result
    return result or (None, None)


def _fetch(location: str) -> tuple[float, float] | None:
    try:
        place = _lookup(location)
    except (GeocoderServiceError, OSError):
        log.warning("geocoding lookup failed for %r", location, exc_info=True)
        return None
    if place is None:
        return None
    return float(place.latitude), float(place.longitude)
