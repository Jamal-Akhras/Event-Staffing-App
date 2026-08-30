import type { WorkerActivity } from "../../types/insights";
import type { CompletedShift, WorkerProfile } from "../../types/operations";

export type Standing = "regular" | "new" | "watch";
export type RosterSort = "reliability" | "shifts" | "recent" | "name";
export type RosterFilter = "all" | "regular" | "new" | "watch";

export type RosterRow = {
  worker: WorkerProfile;
  shiftsWithYou: number;
  lastWorked: string | null;
  rating: number | null;
  standing: Standing;
};

export function buildRoster(
  workers: WorkerProfile[],
  activity: Record<string, WorkerActivity>,
  completed: CompletedShift[]
): RosterRow[] {
  const ratings: Record<string, number[]> = {};
  for (const shift of completed) {
    if (shift.operator_rating === null) continue;
    (ratings[shift.worker_id] ??= []).push(shift.operator_rating);
  }
  return workers.map((worker) => {
    const history = activity[worker.worker_id];
    const shiftsWithYou = history?.completed ?? 0;
    const scores = ratings[worker.worker_id] ?? [];
    return {
      worker,
      shiftsWithYou,
      lastWorked: history?.last_worked ?? null,
      rating: scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null,
      standing: history?.recently_broken ? "watch" : shiftsWithYou >= 3 ? "regular" : "new",
    };
  });
}

export function filterRoster(rows: RosterRow[], query: string, filter: RosterFilter) {
  const needle = query.trim().toLowerCase();
  return rows.filter((row) => {
    if (filter !== "all" && row.standing !== filter) return false;
    if (!needle) return true;
    return [row.worker.display_name, row.worker.role, row.worker.city]
      .join(" ")
      .toLowerCase()
      .includes(needle);
  });
}

export function sortRoster(rows: RosterRow[], sort: RosterSort) {
  return [...rows].sort((left, right) => {
    if (sort === "name") return left.worker.display_name.localeCompare(right.worker.display_name);
    if (sort === "shifts") return right.shiftsWithYou - left.shiftsWithYou;
    if (sort === "recent") {
      return new Date(right.lastWorked ?? 0).getTime() - new Date(left.lastWorked ?? 0).getTime();
    }
    return right.worker.reliability_score - left.worker.reliability_score;
  });
}

export function rosterStats(rows: RosterRow[]) {
  const rated = rows.filter((row) => row.worker.reliability_score > 0);
  const average = rated.length
    ? Math.round((rated.reduce((sum, row) => sum + row.worker.reliability_score, 0) / rated.length) * 100)
    : null;
  return {
    total: rows.length,
    regulars: rows.filter((row) => row.standing === "regular").length,
    watch: rows.filter((row) => row.standing === "watch").length,
    newcomers: rows.filter((row) => row.standing === "new").length,
    averageReliability: average,
  };
}

export const STANDING_LABELS: Record<Standing, string> = {
  regular: "Regular",
  new: "New",
  watch: "Watch",
};
