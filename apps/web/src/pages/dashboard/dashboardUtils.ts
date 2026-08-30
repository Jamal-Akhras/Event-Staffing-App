import type { DayCoverage, TonightShift, WorkerActivity } from "../../types/insights";
import type { Application, Shift, WorkerProfile } from "../../types/operations";

export type CoverageDay = {
  label: string;
  dayNumber: string;
  longLabel: string;
  totalShifts: number;
  openSeats: number;
};

export type TonightRow = {
  shift: Shift;
  names: string[];
  codes: string[];
  missing: number;
};

export type Regular = {
  worker: WorkerProfile;
  completed: number;
};

export function coverageDays(days: DayCoverage[]): CoverageDay[] {
  return days.map((day) => {
    const date = new Date(`${day.day}T00:00:00`);
    return {
      label: date.toLocaleDateString("en-GB", { weekday: "short" }),
      dayNumber: String(date.getDate()),
      longLabel: date.toLocaleDateString("en-GB", { weekday: "long" }),
      totalShifts: day.total_shifts,
      openSeats: day.open_seats,
    };
  });
}

export function describeOpenSeats(days: CoverageDay[]) {
  const parts = days.filter((day) => day.openSeats > 0).map((day) => `${day.openSeats} on ${day.longLabel}`);
  return parts.length ? parts.join(", ") : "Everything this week is covered";
}

export function describeOldest(oldest: string | null, now: Date) {
  if (!oldest) return "Nothing waiting";
  return `Oldest arrived ${relativeTime(new Date(oldest), now)}`;
}

export function tonightRows(tonight: TonightShift[], workers: Record<string, WorkerProfile>): TonightRow[] {
  return tonight.map((row) => ({
    shift: row.shift,
    names: row.workers.map((worker) => workers[worker.worker_id]?.display_name ?? "Booked worker"),
    codes: row.workers.map((worker) => worker.check_in_code ?? ""),
    missing: row.missing,
  }));
}

export function completedCounts(activity: Record<string, WorkerActivity>) {
  return Object.fromEntries(Object.values(activity).map((row) => [row.worker_id, row.completed]));
}

export function regulars(
  activity: Record<string, WorkerActivity>,
  workers: Record<string, WorkerProfile>
): Regular[] {
  return Object.values(activity)
    .filter((row) => row.completed >= 3)
    .map((row) => ({ worker: workers[row.worker_id], completed: row.completed }))
    .filter((entry): entry is Regular => Boolean(entry.worker))
    .sort((left, right) => right.completed - left.completed);
}

export function sortedPending(applications: Application[]) {
  return [...applications].sort(
    (left, right) => new Date(left.created_at).getTime() - new Date(right.created_at).getTime()
  );
}

export function greetingFor(now: Date) {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function timeRange(start: string, end: string) {
  return `${clock(start)} – ${clock(end)}`;
}

export function clock(value: string) {
  return new Date(value).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function shortDay(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { weekday: "short", day: "numeric" });
}

export function relativeTime(then: Date, now: Date) {
  const minutes = Math.max(1, Math.round((now.getTime() - then.getTime()) / 60_000));
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function isSameDay(left: Date, right: Date) {
  return left.toDateString() === right.toDateString();
}
