from __future__ import annotations

from datetime import datetime

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityRule,
    TimeOffRequest,
    TimeOffStatus,
)


class InMemoryAvailabilityRuleRepository:
    def __init__(self) -> None:
        self._rules: dict[str, AvailabilityRule] = {}

    def save(self, rule: AvailabilityRule) -> AvailabilityRule:
        self._rules[rule.rule_id] = rule
        return rule

    def replace_for_worker(
        self, worker_id: str, rules: list[AvailabilityRule]
    ) -> list[AvailabilityRule]:
        self._rules = {
            rule_id: rule for rule_id, rule in self._rules.items() if rule.worker_id != worker_id
        }
        for rule in rules:
            self.save(rule)
        return self.list_for_worker(worker_id)

    def list_for_worker(self, worker_id: str) -> list[AvailabilityRule]:
        return self.list_for_workers([worker_id])

    def list_for_workers(self, worker_ids: list[str]) -> list[AvailabilityRule]:
        wanted = set(worker_ids)
        return sorted(
            (rule for rule in self._rules.values() if rule.worker_id in wanted),
            key=lambda rule: (rule.worker_id, rule.weekday, rule.start_minute, rule.rule_id),
        )

    def clear(self) -> None:
        self._rules.clear()


class InMemoryAvailabilityExceptionRepository:
    def __init__(self) -> None:
        self._exceptions: dict[str, AvailabilityException] = {}

    def save(self, exception: AvailabilityException) -> AvailabilityException:
        self._exceptions[exception.exception_id] = exception
        return exception

    def get(self, exception_id: str) -> AvailabilityException | None:
        return self._exceptions.get(exception_id)

    def delete(self, exception_id: str) -> None:
        self._exceptions.pop(exception_id, None)

    def list_for_worker(self, worker_id: str) -> list[AvailabilityException]:
        return sorted(
            (item for item in self._exceptions.values() if item.worker_id == worker_id),
            key=lambda item: (item.start_time, item.exception_id),
        )

    def list_overlapping_workers(
        self, worker_ids: list[str], start_time: datetime, end_time: datetime
    ) -> list[AvailabilityException]:
        wanted = set(worker_ids)
        return sorted(
            (
                item
                for item in self._exceptions.values()
                if item.worker_id in wanted
                and item.start_time < end_time
                and item.end_time > start_time
            ),
            key=lambda item: (item.start_time, item.exception_id),
        )

    def clear(self) -> None:
        self._exceptions.clear()


class InMemoryTimeOffRepository:
    def __init__(self) -> None:
        self._requests: dict[str, TimeOffRequest] = {}

    def save(self, request: TimeOffRequest) -> TimeOffRequest:
        self._requests[request.request_id] = request
        return request

    def get(self, request_id: str, for_update: bool = False) -> TimeOffRequest | None:
        return self._requests.get(request_id)

    def list_for_worker(self, worker_id: str) -> list[TimeOffRequest]:
        return self._ordered(item for item in self._requests.values() if item.worker_id == worker_id)

    def list_for_venue(
        self,
        venue_id: str,
        status: TimeOffStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TimeOffRequest]:
        items = [item for item in self._requests.values() if item.venue_id == venue_id]
        if status is not None:
            items = [item for item in items if item.status == status]
        if start_time is not None:
            items = [item for item in items if item.end_time > start_time]
        if end_time is not None:
            items = [item for item in items if item.start_time < end_time]
        return self._ordered(items)

    def list_overlapping_workers(
        self,
        worker_ids: list[str],
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
        statuses: tuple[TimeOffStatus, ...] | None = None,
    ) -> list[TimeOffRequest]:
        wanted = set(worker_ids)
        return self._ordered(
            item
            for item in self._requests.values()
            if item.worker_id in wanted
            and item.start_time < end_time
            and item.end_time > start_time
            and (venue_id is None or item.venue_id == venue_id)
            and (statuses is None or item.status in statuses)
        )

    def clear(self) -> None:
        self._requests.clear()

    @staticmethod
    def _ordered(items) -> list[TimeOffRequest]:
        return sorted(items, key=lambda item: (item.start_time, item.request_id))
