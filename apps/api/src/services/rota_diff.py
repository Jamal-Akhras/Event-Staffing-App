from __future__ import annotations

from typing import Any

from apps.api.src.models.shift import Shift


def _entry(shift: Shift, worker_id: str) -> dict[str, Any]:
    return {
        "shift_id": shift.shift_id,
        "worker_id": worker_id,
        "role": shift.role,
        "start_time": shift.start_time.isoformat(),
        "end_time": shift.end_time.isoformat(),
    }


def _normalize(entries: list[dict[str, Any]]) -> list[tuple]:
    return sorted(
        (e["shift_id"], e["worker_id"], e["start_time"], e["end_time"]) for e in entries
    )


def _diff(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prev_by_shift: dict[str, list[dict[str, Any]]] = {}
    for entry in previous:
        prev_by_shift.setdefault(entry["shift_id"], []).append(entry)
    curr_by_shift: dict[str, list[dict[str, Any]]] = {}
    for entry in current:
        curr_by_shift.setdefault(entry["shift_id"], []).append(entry)

    changes: list[dict[str, Any]] = []
    for shift_id, entries in curr_by_shift.items():
        before = prev_by_shift.get(shift_id, [])
        before_workers = {e["worker_id"]: e for e in before}
        for entry in entries:
            prior = before_workers.get(entry["worker_id"])
            if prior is None:
                others = [e for e in before if e["worker_id"] not in {c["worker_id"] for c in entries}]
                if len(before) == 1 and len(entries) == 1 and others:
                    changes.append({
                        "kind": "reassigned", "shift_id": shift_id, "role": entry["role"],
                        "worker_id": entry["worker_id"], "previous_worker_id": before[0]["worker_id"],
                        "start_time": entry["start_time"], "end_time": entry["end_time"],
                    })
                else:
                    changes.append({
                        "kind": "added", "shift_id": shift_id, "role": entry["role"],
                        "worker_id": entry["worker_id"],
                        "start_time": entry["start_time"], "end_time": entry["end_time"],
                    })
            elif (prior["start_time"], prior["end_time"]) != (entry["start_time"], entry["end_time"]):
                changes.append({
                    "kind": "time_changed", "shift_id": shift_id, "role": entry["role"],
                    "worker_id": entry["worker_id"],
                    "start_time": entry["start_time"], "end_time": entry["end_time"],
                    "previous_start_time": prior["start_time"], "previous_end_time": prior["end_time"],
                })
    for shift_id, entries in prev_by_shift.items():
        current_workers = {e["worker_id"] for e in curr_by_shift.get(shift_id, [])}
        reassigned_from = {
            c.get("previous_worker_id") for c in changes if c["shift_id"] == shift_id
        }
        for entry in entries:
            if entry["worker_id"] not in current_workers and entry["worker_id"] not in reassigned_from:
                changes.append({
                    "kind": "removed", "shift_id": shift_id, "role": entry["role"],
                    "worker_id": entry["worker_id"],
                    "start_time": entry["start_time"], "end_time": entry["end_time"],
                })
    return sorted(changes, key=lambda c: (c["shift_id"], c["kind"], c.get("worker_id") or ""))
