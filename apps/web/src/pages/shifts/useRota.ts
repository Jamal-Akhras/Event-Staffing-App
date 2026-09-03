import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson, postJson } from "../../lib/api";
import { idempotencyHeaders, requestAttempt, type IdempotencyAttempt } from "../../lib/idempotency";
import type { RotaPublication, RotaPublishResult } from "../../types/rota";

type Notify = (type: "success" | "error", message: string) => void;

export function usePublications(weekStart: string, enabled = true) {
  return useQuery({
    queryKey: ["rota-publications", weekStart],
    queryFn: () => fetchJson<RotaPublication[]>(`/venues/me/rota/publications?week_start=${weekStart}`),
    enabled,
  });
}

export function useRotaActions(weekStart: string, notify: Notify) {
  const client = useQueryClient();
  const publishAttempt = useRef<IdempotencyAttempt | null>(null);

  const settle = async (message: string) => {
    await Promise.all(
      ["shifts", "bookings", "applications", "rota-publications"].map((key) =>
        client.invalidateQueries({ queryKey: [key] })
      )
    );
    notify("success", message);
  };
  const fail = (error: Error) => notify("error", error.message);

  const publish = useMutation({
    mutationFn: () => {
      const payload = { week_start: weekStart };
      publishAttempt.current = requestAttempt(publishAttempt.current, JSON.stringify(payload));
      return postJson<RotaPublishResult>(
        "/venues/me/rota/publish",
        payload,
        idempotencyHeaders(publishAttempt.current),
      );
    },
    onSuccess: (result) => {
      publishAttempt.current = null;
      const booked = result.booked_worker_ids.length;
      const offered = result.offered_worker_ids.length;
      settle(
        booked + offered === 0
          ? "Week published — no changes since the last revision."
          : `Week published: ${booked} booked, ${offered} offered.`
      );
    },
    onError: fail,
  });

  const updateTimes = useMutation({
    mutationFn: (input: { shiftId: string; start: string; end: string }) =>
      postJson(`/venues/me/rota/shifts/${input.shiftId}/times`, {
        start_time: input.start,
        end_time: input.end,
        now: new Date().toISOString(),
      }),
    onSuccess: () => settle("Times updated and the worker notified."),
    onError: fail,
  });

  const reassign = useMutation({
    mutationFn: (input: { shiftId: string; workerId: string }) =>
      postJson(`/venues/me/rota/shifts/${input.shiftId}/reassign`, {
        worker_id: input.workerId,
        now: new Date().toISOString(),
      }),
    onSuccess: () => settle("Shift reassigned — both workers notified."),
    onError: fail,
  });

  const remove = useMutation({
    mutationFn: (input: { shiftId: string; reason: string }) =>
      postJson(`/venues/me/rota/shifts/${input.shiftId}/remove`, {
        reason: input.reason,
        now: new Date().toISOString(),
      }),
    onSuccess: () => settle("Shift removed from the rota."),
    onError: fail,
  });

  return { publish, updateTimes, reassign, remove };
}
