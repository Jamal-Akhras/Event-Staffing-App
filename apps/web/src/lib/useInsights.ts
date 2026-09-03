import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "./api";
import type {
  AnalyticsPeriod,
  RosterActivity,
  VenueAnalytics,
  VenueOverview,
  WorkerActivity,
} from "../types/insights";
import type { Shift } from "../types/operations";

export function startOfDay(now: Date) {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  return start;
}

export function startOfMonth(now: Date) {
  return new Date(now.getFullYear(), now.getMonth(), 1);
}

export function daysInMonth(now: Date) {
  return new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
}

export function useVenueOverview(windowStart: Date, days: number, enabled = true) {
  const start = windowStart.toISOString();
  return useQuery({
    queryKey: ["insights-overview", start, days],
    queryFn: () =>
      fetchJson<VenueOverview>(`/insights/overview?window_start=${encodeURIComponent(start)}&days=${days}`),
    enabled,
  });
}

export function useRosterActivity() {
  return useQuery({
    queryKey: ["insights-roster"],
    queryFn: async () => {
      const payload = await fetchJson<RosterActivity>("/insights/roster");
      return Object.fromEntries(payload.workers.map((row) => [row.worker_id, row])) as Record<
        string,
        WorkerActivity
      >;
    },
  });
}

export function useShiftsInRange(start: Date, end: Date, enabled = true) {
  const from = start.toISOString();
  const before = end.toISOString();
  return useQuery({
    queryKey: ["shifts", from, before],
    queryFn: () =>
      fetchJson<Shift[]>(
        `/shifts?starts_from=${encodeURIComponent(from)}&starts_before=${encodeURIComponent(before)}`
      ),
    enabled,
  });
}

export function useVenueAnalytics(period: AnalyticsPeriod) {
  return useQuery({
    queryKey: ["insights-analytics", period],
    queryFn: () => fetchJson<VenueAnalytics>(`/insights/analytics?period=${period}`),
  });
}
