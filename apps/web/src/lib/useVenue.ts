import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "./api";
import type { Venue, VenueRatingSummary } from "../types/operations";

export function useVenue() {
  return useQuery({ queryKey: ["venue"], queryFn: () => fetchJson<Venue>("/venues/me") });
}

export function useVenueRating(venueId?: string) {
  return useQuery({
    queryKey: ["venue-rating", venueId],
    queryFn: () => fetchJson<VenueRatingSummary>(`/venues/${venueId}/rating-summary`),
    enabled: Boolean(venueId),
  });
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}
