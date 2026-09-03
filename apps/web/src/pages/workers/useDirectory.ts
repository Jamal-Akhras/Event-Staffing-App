import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteJson, fetchJson, postJson, putJson } from "../../lib/api";
import type { EmployedType } from "../../types/workforce";
import type { DirectoryEntry } from "./directory";

const KEY = ["venue-people"];

type Notify = (type: "success" | "error", message: string) => void;

export function usePeople() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => fetchJson<DirectoryEntry[]>("/venues/me/people"),
  });
}

export type TermsInput = {
  workerId: string;
  agreed_rate: string | null;
  contracted_hours_per_week: string | null;
  default_role: string | null;
};

export function useDirectory(notify: Notify) {
  const client = useQueryClient();
  const people = usePeople();

  const settle = (message: string) => {
    client.invalidateQueries({ queryKey: KEY });
    notify("success", message);
  };
  const fail = (error: Error) => notify("error", error.message);

  const addToPool = useMutation({
    mutationFn: (workerId: string) => postJson(`/venues/me/people/${workerId}/pool`),
    onSuccess: () => settle("Added to your team"),
    onError: fail,
  });

  const removeFromPool = useMutation({
    mutationFn: (workerId: string) => deleteJson(`/venues/me/people/${workerId}/pool`),
    onSuccess: () => settle("Removed from your team"),
    onError: fail,
  });

  const invite = useMutation({
    mutationFn: (input: { workerId: string; relationship_type: EmployedType }) =>
      postJson(`/venues/me/people/${input.workerId}/invite`, {
        relationship_type: input.relationship_type,
      }),
    onSuccess: () => settle("Invitation sent — they choose whether to accept"),
    onError: fail,
  });

  const end = useMutation({
    mutationFn: (workerId: string) => postJson(`/venues/me/people/${workerId}/end`, {}),
    onSuccess: () => settle("Relationship ended"),
    onError: fail,
  });

  const setTerms = useMutation({
    mutationFn: ({ workerId, ...terms }: TermsInput) =>
      putJson(`/venues/me/people/${workerId}/terms`, terms),
    onSuccess: () => settle("Terms saved"),
    onError: fail,
  });

  return { people, addToPool, removeFromPool, invite, end, setTerms };
}
