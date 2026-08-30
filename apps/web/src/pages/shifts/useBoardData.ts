import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "../../lib/api";
import { startOfDay, useRosterActivity, useShiftsInRange, useVenueOverview } from "../../lib/useInsights";
import type { Application, Booking, WorkerProfile } from "../../types/operations";
import { nextDay } from "./boardUtils";

const WEEK_DAYS = 7;

export function useBoardData(days: Date[], now: Date) {
  const shifts = useShiftsInRange(days[0], nextDay(days[days.length - 1]));
  const overview = useVenueOverview(startOfDay(now), WEEK_DAYS);
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
      ...(overview.data?.tonight ?? []).flatMap((row) => row.workers.map((worker) => worker.worker_id)),
    ])
  ).sort();
  const workers = useQuery({
    queryKey: ["workers", workerIds],
    enabled: applications.isSuccess && bookings.isSuccess && overview.isSuccess,
    queryFn: async () => {
      const profiles = await Promise.all(workerIds.map((id) => fetchJson<WorkerProfile>(`/workers/${id}`)));
      return Object.fromEntries(profiles.map((profile) => [profile.worker_id, profile]));
    },
  });

  const queries = [shifts, overview, activity, applications, bookings, workers];
  const error = queries.find((query) => query.error)?.error as Error | undefined;

  return {
    loading: queries.some((query) => query.isPending && query.fetchStatus !== "idle"),
    error,
    shifts: shifts.data ?? [],
    overview: overview.data,
    activity: activity.data ?? {},
    applications: applications.data ?? [],
    bookings: bookings.data ?? [],
    workers: workers.data ?? {},
  };
}
