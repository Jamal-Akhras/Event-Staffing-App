import { useQuery } from "@tanstack/react-query";

import { useAuth, type SessionPayload } from "../contexts/AuthContext";
import { fetchJson, postJson } from "../lib/api";

type VenueSummary = {
  venue_id: string;
  name: string;
};

export function VenueSwitcher() {
  const { user, acceptSession } = useAuth();
  const venues = useQuery({
    queryKey: ["my-venues"],
    queryFn: () => fetchJson<VenueSummary[]>("/venues"),
  });

  const rows = venues.data ?? [];
  if (rows.length < 2) return null;

  const current = user?.account_id ?? "";

  const switchTo = async (venueId: string) => {
    if (!venueId || venueId === current) return;
    const session = await postJson<SessionPayload>("/auth/switch-venue", { venue_id: venueId });
    acceptSession(session);
    window.location.reload();
  };

  return (
    <select
      className="venue-switcher"
      value={current}
      onChange={(event) => void switchTo(event.target.value)}
      aria-label="Switch venue"
    >
      {rows.map((venue) => (
        <option key={venue.venue_id} value={venue.venue_id}>
          {venue.name}
        </option>
      ))}
    </select>
  );
}
