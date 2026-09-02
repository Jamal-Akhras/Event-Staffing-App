import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteJson, fetchJson, postJson } from "../../lib/api";
import type { EmployedType, JoinCode } from "../../types/workforce";

const KEY = ["join-codes"];

export type NewJoinCode = {
  relationship_type: EmployedType;
  default_role: string | null;
  max_redemptions: number;
};

export function useJoinCodes(notify: (type: "success" | "error", message: string) => void) {
  const client = useQueryClient();
  const codes = useQuery({
    queryKey: KEY,
    queryFn: () => fetchJson<JoinCode[]>("/venues/me/join-codes"),
  });

  const settle = (message: string) => {
    client.invalidateQueries({ queryKey: KEY });
    notify("success", message);
  };

  const create = useMutation({
    mutationFn: (payload: NewJoinCode) => postJson<JoinCode>("/venues/me/join-codes", payload),
    onSuccess: (code) => settle(`Code ${code.code} is ready to share`),
    onError: (error: Error) => notify("error", error.message),
  });

  const revoke = useMutation({
    mutationFn: (code: string) => deleteJson(`/venues/me/join-codes/${code}`),
    onSuccess: () => settle("Code turned off"),
    onError: (error: Error) => notify("error", error.message),
  });

  const live = (codes.data ?? []).filter((code) => !code.revoked_at && code.redeemed < code.max_redemptions);

  return { codes, live, create, revoke };
}
