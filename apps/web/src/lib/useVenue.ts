import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "./api";
import type { Venue } from "../types/operations";

export function useVenue() {
  return useQuery({ queryKey: ["venue"], queryFn: () => fetchJson<Venue>("/venues/me") });
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}
