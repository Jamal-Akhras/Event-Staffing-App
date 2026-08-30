import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "../../lib/api";
import { startOfDay, useRosterActivity, useShiftsInRange } from "../../lib/useInsights";
import type { Application, Booking, WorkerProfile } from "../../types/operations";

const HISTORY_DAYS = 30;
const HORIZON_DAYS = 92;

export function operationsWindow(now: Date) {
  const start = startOfDay(now);
  const from = new Date(start);
  from.setDate(from.getDate() - HISTORY_DAYS);
  const before = new Date(start);
  before.setDate(before.getDate() + HORIZON_DAYS);
  return { from, before };
}

export function useOperationsData(now: Date) {
  const { from, before } = operationsWindow(now);
  const shifts = useShiftsInRange(from, before);
  const activity = useRosterActivity();
  const applications = useQuery({
    queryKey: ["applications"],
    queryFn: () => fetchJson<Application[]>("/applications?limit=100"),
  });
  const bookings = useQuery({
    queryKey: ["bookings"],
    queryFn: () => fetchJson<Booking[]>("/bookings?limit=100"),
  });

  const workerIds = Array.from(
    new Set([
      ...(applications.data ?? []).map((application) => application.worker_id),
      ...(bookings.data ?? []).map((booking) => booking.worker_id),
    ])
  ).sort();
  const workers = useQuery({
    queryKey: ["workers", workerIds],
    enabled: applications.isSuccess && bookings.isSuccess,
    queryFn: async () => {
      const profiles = await Promise.all(workerIds.map((id) => fetchJson<WorkerProfile>(`/workers/${id}`)));
      return Object.fromEntries(profiles.map((profile) => [profile.worker_id, profile]));
    },
  });

  const queries = [shifts, activity, applications, bookings, workers];
  const error = queries.find((query) => query.error)?.error as Error | undefined;
  const loading = queries.some((query) => query.isPending && query.fetchStatus !== "idle");

  return {
    loading,
    error,
    shifts: shifts.data ?? [],
    activity: activity.data ?? {},
    applications: applications.data ?? [],
    bookings: bookings.data ?? [],
    workers: workers.data ?? {},
  };
}
