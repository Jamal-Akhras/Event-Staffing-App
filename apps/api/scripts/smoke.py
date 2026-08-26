from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from typing import Any
from uuid import uuid4

BASE = "http://127.0.0.1:8001"

OK = "\033[32mOK \033[0m"
FAIL = "\033[31mFAIL\033[0m"

failures: list[tuple[str, int, str]] = []


def call(method: str, path: str, *, body: dict | None = None, headers: dict | None = None) -> tuple[int, Any]:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = resp.read().decode()
            return resp.status, _decode(payload)
    except urllib.error.HTTPError as e:
        return e.code, _decode(e.read().decode())
    except Exception as e:
        return 0, str(e)


def _decode(text: str) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def probe(label: str, method: str, path: str, *, body: dict | None = None, headers: dict | None = None, expected: set[int] = {200, 201}) -> tuple[int, Any]:
    status, payload = call(method, path, body=body, headers=headers)
    if status in expected:
        print(f"  {OK} {method:6s} {path:48s} {status}")
    else:
        print(f"  {FAIL} {method:6s} {path:48s} {status}  {label}  {str(payload)[:160]}")
        failures.append((f"{method} {path}", status, str(payload)[:200]))
    return status, payload


def main() -> int:
    print("== health ==")
    probe("health", "GET", "/health")

    print("\n== operator register + login ==")
    operator_email = f"smoke-op-{uuid4().hex[:6]}@example.com"
    s, body = probe("register operator", "POST", "/auth/register/operator", body={
        "email": operator_email, "password": "smoke-pass-12", "venue_name": "Smoke Venue",
        "country": "GB", "market_id": "bath-gb",
    })
    operator_token = body.get("access_token") if isinstance(body, dict) else None
    operator_account = body.get("account_id") if isinstance(body, dict) else None
    operator_id = body.get("user_id") if isinstance(body, dict) else None
    op_h = {"Authorization": f"Bearer {operator_token}"} if operator_token else {}

    print("\n== worker register ==")
    worker_email = f"smoke-w-{uuid4().hex[:6]}@example.com"
    s, body = probe("register worker", "POST", "/auth/register", body={
        "email": worker_email, "password": "smoke-pass-12",
    })
    worker_token = body.get("access_token") if isinstance(body, dict) else None
    worker_id = body.get("worker_profile_id") if isinstance(body, dict) else None
    w_h = {"Authorization": f"Bearer {worker_token}"} if worker_token else {}

    print("\n== operator surfaces ==")
    probe("accounts me", "GET", "/accounts/me", headers=op_h)
    probe("shifts list (operator)", "GET", "/shifts", headers=op_h)
    probe("applications list (operator)", "GET", "/applications", headers=op_h)
    probe("workers list (operator)", "GET", "/workers", headers=op_h)
    probe("bookings list (operator)", "GET", "/bookings", headers=op_h)
    probe("templates list", "GET", "/templates", headers=op_h)
    probe("completed shifts", "GET", "/accounts/me/completed-shifts", headers=op_h)

    print("\n== operator: post shift ==")
    s, body = probe("create shift", "POST", "/shifts", body={
        "role": "Server",
        "location": "Downtown",
        "start_time": "2030-06-01T18:00:00",
        "end_time": "2030-06-01T22:00:00",
        "pay_rate": 14.5,
        "workers_needed": 2,
        "notes": "Smoke shift",
    }, headers=op_h)
    shift_id = body.get("shift_id") if isinstance(body, dict) else None

    print("\n== worker surfaces ==")
    probe("auth me (worker)", "GET", "/auth/me", headers=w_h)
    probe("shifts list (worker)", "GET", "/shifts", headers=w_h)
    if worker_id:
        probe("worker profile", "GET", f"/workers/{worker_id}", headers=w_h)
        probe("worker earnings week", "GET", f"/workers/{worker_id}/earnings?period=week", headers=w_h)
        probe("worker earnings month", "GET", f"/workers/{worker_id}/earnings?period=month", headers=w_h)
        probe("worker notifications", "GET", f"/workers/{worker_id}/notifications", headers=w_h)
        probe("worker feed-state", "GET", f"/workers/{worker_id}/feed-state", headers=w_h)
        probe("worker rating-summary", "GET", f"/workers/{worker_id}/rating-summary", headers=op_h)

    print("\n== worker applies, operator approves ==")
    if shift_id and worker_id:
        s, body = probe("apply", "POST", "/applications", body={
            "shift_id": shift_id, "worker_id": worker_id, "message": "smoke",
        }, headers=w_h)
        application_id = body.get("application_id") if isinstance(body, dict) else None
        if application_id:
            probe("approve", "POST", f"/applications/{application_id}/approve", body={}, headers=op_h)

    print("\n== auth/me both ==")
    probe("auth me (operator)", "GET", "/auth/me", headers=op_h)

    print("\n== shift detail ==")
    if shift_id:
        probe("shift detail (operator)", "GET", f"/shifts/{shift_id}", headers=op_h)

    print()
    if failures:
        print(f"{FAIL} {len(failures)} failure(s):")
        for path, status, snippet in failures:
            print(f"  {status} {path}  ::  {snippet}")
        return 1
    print(f"{OK} all probes OK ({sum(1 for _ in range(0))} failures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
