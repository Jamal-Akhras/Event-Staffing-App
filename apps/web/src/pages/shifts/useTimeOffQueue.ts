import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson, postJson } from "../../lib/api";
import { idempotencyHeaders, requestAttempt, type IdempotencyAttempt } from "../../lib/idempotency";
import type { TimeOffRequest } from "../../types/workforce";

type Decision = { requestId: string; action: "approve" | "decline" };
type Notify = (type: "success" | "error", message: string) => void;

export function useTimeOffQueue(notify: Notify) {
  const client = useQueryClient();
  const attempts = useRef(new Map<string, IdempotencyAttempt>());
  const query = useQuery({
    queryKey: ["time-off", "pending"],
    queryFn: () => fetchJson<TimeOffRequest[]>("/venues/me/time-off?status=pending"),
  });
  const decision = useMutation({
    mutationFn: ({ requestId, action }: Decision) => {
      const fingerprint = `${action}:${requestId}`;
      const attempt = requestAttempt(attempts.current.get(fingerprint) ?? null, fingerprint);
      attempts.current.set(fingerprint, attempt);
      return postJson<TimeOffRequest>(
        `/venues/me/time-off/${requestId}/${action}`,
        undefined,
        idempotencyHeaders(attempt),
      );
    },
    onSuccess: async (_, variables) => {
      attempts.current.delete(`${variables.action}:${variables.requestId}`);
      await client.invalidateQueries({ queryKey: ["time-off"] });
      notify(
        "success",
        variables.action === "approve" ? "Time off approved." : "Time off declined.",
      );
    },
    onError: (error: Error) => notify("error", error.message),
  });
  return { query, decision };
}
