import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson, postJson } from "../../lib/api";
import type { Application, Booking, Shift, WorkerProfile } from "../../types/operations";

export function useOverviewData() {
  const shifts = useQuery({ queryKey: ["shifts"], queryFn: () => fetchJson<Shift[]>("/shifts?limit=100") });
  const applications = useQuery({
    queryKey: ["applications"],
    queryFn: () => fetchJson<Application[]>("/applications?limit=100"),
  });
  const bookings = useQuery({ queryKey: ["bookings"], queryFn: () => fetchJson<Booking[]>("/bookings?limit=100") });

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

  const queries = [shifts, applications, bookings, workers];
  const error = queries.find((query) => query.error)?.error as Error | undefined;
  const loading = queries.some((query) => query.isPending && query.fetchStatus !== "idle");

  return {
    loading,
    error,
    shifts: shifts.data ?? [],
    applications: applications.data ?? [],
    bookings: bookings.data ?? [],
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
      onDone(action === "approve" ? "Application approved." : "Application declined.");
    },
    onError: (error: Error) => onError(error.message),
  });
}
