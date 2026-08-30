import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson, postJson } from "../../lib/api";
import { startOfDay, useRosterActivity, useVenueOverview } from "../../lib/useInsights";
import type { Application, WorkerProfile } from "../../types/operations";

const WEEK_DAYS = 7;

export function useOverviewData(now: Date) {
  const overview = useVenueOverview(startOfDay(now), WEEK_DAYS);
  const activity = useRosterActivity();
  const pending = useQuery({
    queryKey: ["applications", "applied"],
    queryFn: () => fetchJson<Application[]>("/applications?status=applied&limit=100"),
  });

  const workerIds = Array.from(
    new Set([
      ...(pending.data ?? []).map((application) => application.worker_id),
      ...(overview.data?.tonight ?? []).flatMap((row) => row.workers.map((worker) => worker.worker_id)),
      ...Object.keys(activity.data ?? {}),
    ])
  ).sort();
  const workers = useQuery({
    queryKey: ["workers", workerIds],
    enabled: pending.isSuccess && overview.isSuccess && activity.isSuccess,
    queryFn: async () => {
      const profiles = await Promise.all(workerIds.map((id) => fetchJson<WorkerProfile>(`/workers/${id}`)));
      return Object.fromEntries(profiles.map((profile) => [profile.worker_id, profile]));
    },
  });

  const queries = [overview, activity, pending, workers];
  const error = queries.find((query) => query.error)?.error as Error | undefined;
  const loading = queries.some((query) => query.isPending && query.fetchStatus !== "idle");

  return {
    loading,
    error,
    overview: overview.data,
    activity: activity.data ?? {},
    pending: pending.data ?? [],
    workers: workers.data ?? {},
    refetch: () => Promise.all(queries.map((query) => query.refetch())),
  };
}

export function useDecideApplication(onDone: (message: string) => void, onError: (message: string) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicationId, action }: { applicationId: string; action: "approve" | "reject" }) =>
      postJson(`/applications/${applicationId}/${action}`, { now: new Date().toISOString() }),
    onSuccess: async (_result, { action }) => {
      await queryClient.invalidateQueries({ queryKey: ["applications"] });
      await queryClient.invalidateQueries({ queryKey: ["shifts"] });
      await queryClient.invalidateQueries({ queryKey: ["bookings"] });
      await queryClient.invalidateQueries({ queryKey: ["insights-overview"] });
      await queryClient.invalidateQueries({ queryKey: ["insights-roster"] });
      onDone(action === "approve" ? "Application approved." : "Application declined.");
    },
    onError: (error: Error) => onError(error.message),
  });
}
