from __future__ import annotations

import base64
from dataclasses import asdict
from datetime import datetime
import hashlib
import hmac
import json

from apps.api.src.auth.jwt import JWT_SECRET_KEY
from apps.api.src.datetime_utils import normalize_utc
from apps.api.src.models.worker_feed_query import FeedPosition


class FeedCursorError(ValueError):
    pass


def filter_fingerprint(
    search: str | None,
    timing: str,
    minimum_pay: str | None,
) -> str:
    value = json.dumps(
        {"search": search, "timing": timing, "minimum_pay": minimum_pay},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(value.encode()).hexdigest()


def encode_feed_cursor(
    position: FeedPosition,
    worker_id: str,
    market_id: str,
    fingerprint: str,
) -> str:
    payload = {
        "position": {
            **asdict(position),
            "start_time": normalize_utc(position.start_time).isoformat(),
        },
        "worker_id": worker_id,
        "market_id": market_id,
        "fingerprint": fingerprint,
    }
    body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _encode(hmac.digest(JWT_SECRET_KEY.encode(), body.encode(), "sha256"))
    return f"{body}.{signature}"


def decode_feed_cursor(
    cursor: str,
    worker_id: str,
    market_id: str,
    fingerprint: str,
) -> FeedPosition:
    try:
        body, supplied_signature = cursor.split(".", maxsplit=1)
        expected_signature = _encode(hmac.digest(JWT_SECRET_KEY.encode(), body.encode(), "sha256"))
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise FeedCursorError("Invalid feed cursor.")
        payload = json.loads(_decode(body))
        if payload["worker_id"] != worker_id or payload["market_id"] != market_id:
            raise FeedCursorError("Invalid feed cursor.")
        if payload["fingerprint"] != fingerprint:
            raise FeedCursorError("Feed cursor does not match the active filters.")
        position = payload["position"]
        return FeedPosition(
            start_time=normalize_utc(datetime.fromisoformat(position["start_time"])),
            shift_id=position["shift_id"],
        )
    except FeedCursorError:
        raise
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FeedCursorError("Invalid feed cursor.") from exc


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode()
