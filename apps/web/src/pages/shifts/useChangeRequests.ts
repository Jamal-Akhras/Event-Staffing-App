import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchJson, postJson } from "../../lib/api";
import { idempotencyHeaders, requestAttempt, type IdempotencyAttempt } from "../../lib/idempotency";
import type { ShiftChangeRequest } from "../../types/workforce";

type Decision = { requestId: string; action: "approve" | "decline" };
type Notify = (type: "success" | "error", message: string) => void;

export function useChangeRequests(notify: Notify) {
  const client = useQueryClient();
  const attempts = useRef(new Map<string, IdempotencyAttempt>());
  const query = useQuery({
    queryKey: ["shift-changes", "pending_manager"],
    queryFn: () =>
      fetchJson<ShiftChangeRequest[]>("/venues/me/shift-change-requests?status=pending_manager"),
  });
  const decision = useMutation({
    mutationFn: ({ requestId, action }: Decision) => {
      const fingerprint = `${action}:${requestId}`;
      const attempt = requestAttempt(attempts.current.get(fingerprint) ?? null, fingerprint);
      attempts.current.set(fingerprint, attempt);
      return postJson<ShiftChangeRequest>(
        `/venues/me/shift-change-requests/${requestId}/${action}`,
        {},
        idempotencyHeaders(attempt),
      );
    },
    onSuccess: async (_, variables) => {
      attempts.current.delete(`${variables.action}:${variables.requestId}`);
      await client.invalidateQueries({ queryKey: ["shift-changes"] });
      await client.invalidateQueries({ queryKey: ["board"] });
      notify(
        "success",
        variables.action === "approve" ? "Change approved." : "Change declined.",
      );
    },
    onError: (error: Error) => notify("error", error.message),
  });
  return { query, decision };
}
