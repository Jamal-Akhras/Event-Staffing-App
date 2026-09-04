import type { RelationshipType } from "../../types/workforce";

export type DirectoryEntry = {
  worker_id: string;
  display_name: string;
  role: string;
  relationship_id: string;
  relationship_type: RelationshipType;
  status: "invited" | "active" | "ended";
  agreed_rate: string | null;
  contracted_hours_per_week: string | null;
  start_date: string | null;
  end_date: string | null;
  reliability_score: number;
  avatar_url: string | null;
  allows_recontact: boolean;
  shifts_with_you: number;
  hours_with_you: string;
  wages_to_date: string;
  fees_to_date: string;
  last_worked: string | null;
  current_status: "booked" | "away" | "unavailable" | "available";
  availability_configured: boolean;
};

export type DirectoryFilter = "all" | "team" | "pool" | "once" | "ended";
export type DirectorySort = "name" | "shifts" | "recent" | "reliability";

export const FILTERS: { key: DirectoryFilter; label: string }[] = [
  { key: "all", label: "Everyone" },
  { key: "team", label: "Your team" },
  { key: "pool", label: "Your pool" },
  { key: "once", label: "Worked once" },
  { key: "ended", label: "Past" },
];

export function bucketOf(entry: DirectoryEntry): DirectoryFilter {
  if (entry.status === "ended") return "ended";
  if (entry.relationship_type === "pool") return "pool";
  if (entry.relationship_type === "one_off") return "once";
  return "team";
}

export function filterDirectory(entries: DirectoryEntry[], query: string, filter: DirectoryFilter) {
  const needle = query.trim().toLowerCase();
  return entries.filter((entry) => {
    if (filter !== "all" && bucketOf(entry) !== filter) return false;
    if (!needle) return true;
    return `${entry.display_name} ${entry.role}`.toLowerCase().includes(needle);
  });
}

export function sortDirectory(entries: DirectoryEntry[], sort: DirectorySort) {
  return [...entries].sort((left, right) => {
    if (sort === "shifts") return right.shifts_with_you - left.shifts_with_you;
    if (sort === "recent") {
      return new Date(right.last_worked ?? 0).getTime() - new Date(left.last_worked ?? 0).getTime();
    }
    if (sort === "reliability") return right.reliability_score - left.reliability_score;
    return left.display_name.localeCompare(right.display_name);
  });
}

export function directoryCounts(entries: DirectoryEntry[]): Record<DirectoryFilter, number> {
  const counts: Record<DirectoryFilter, number> = { all: entries.length, team: 0, pool: 0, once: 0, ended: 0 };
  for (const entry of entries) counts[bucketOf(entry)] += 1;
  return counts;
}

export function directoryStats(entries: DirectoryEntry[]) {
  const counts = directoryCounts(entries);
  const wages = entries.reduce((sum, entry) => sum + Number(entry.wages_to_date), 0);
  const fees = entries.reduce((sum, entry) => sum + Number(entry.fees_to_date), 0);
  return { counts, wages, fees, invited: entries.filter((entry) => entry.status === "invited").length };
}

export function statusLabel(entry: DirectoryEntry): string | null {
  if (entry.status !== "active") return null;
  if (entry.current_status === "booked") return "Working now";
  if (entry.current_status === "away") return "Away";
  if (entry.current_status === "unavailable") return "Not available today";
  if (!entry.availability_configured) return null;
  return "Available";
}
