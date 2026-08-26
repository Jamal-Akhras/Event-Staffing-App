import type { Application, Booking, Shift, WorkerProfile } from "../../types/operations";

const COMPLETED = new Set(["checked_out", "approved", "paid"]);
const ACTIVE = new Set(["requested", "confirmed", "checked_in", "checked_out", "approved", "paid"]);
const DAY_MS = 24 * 60 * 60 * 1000;

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

export function liveShifts(shifts: Shift[]) {
  return shifts.filter((shift) => shift.status !== "cancelled");
}

export function getOpenSeats(shifts: Shift[]) {
  return shifts.reduce((sum, shift) => sum + Math.max(shift.workers_needed - shift.workers_filled, 0), 0);
}

export function buildCoverageDays(shifts: Shift[], now: Date): CoverageDay[] {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(now);
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + index);
    const dayShifts = shifts.filter((shift) => isSameDay(new Date(shift.start_time), date));
    return {
      label: date.toLocaleDateString("en-GB", { weekday: "short" }),
      dayNumber: String(date.getDate()),
      longLabel: date.toLocaleDateString("en-GB", { weekday: "long" }),
      totalShifts: dayShifts.length,
      openSeats: getOpenSeats(dayShifts.filter((shift) => shift.status === "open")),
    };
  });
}

export function describeOpenSeats(days: CoverageDay[]) {
  const parts = days.filter((day) => day.openSeats > 0).map((day) => `${day.openSeats} on ${day.longLabel}`);
  return parts.length ? parts.join(", ") : "Everything this week is covered";
}

export function pendingApplications(applications: Application[]) {
  return applications
    .filter((application) => application.status === "applied")
    .sort((left, right) => new Date(left.created_at).getTime() - new Date(right.created_at).getTime());
}

export function describeOldest(pending: Application[], now: Date) {
  if (!pending.length) return "Nothing waiting";
  return `Oldest arrived ${relativeTime(new Date(pending[0].created_at), now)}`;
}

export function attendance(bookings: Booking[], now: Date) {
  const since = now.getTime() - 30 * DAY_MS;
  const recent = bookings.filter((booking) => {
    const start = new Date(booking.start_time).getTime();
    return start >= since && start <= now.getTime();
  });
  const completed = recent.filter((booking) => COMPLETED.has(booking.state)).length;
  const noShows = recent.filter((booking) => booking.state === "no_show").length;
  const total = completed + noShows;
  return { rate: total ? Math.round((completed / total) * 100) : null, total };
}

export function tonightRows(
  shifts: Shift[],
  bookings: Booking[],
  workers: Record<string, WorkerProfile>,
  now: Date
): TonightRow[] {
  return shifts
    .filter((shift) => isSameDay(new Date(shift.start_time), now))
    .sort((left, right) => new Date(left.start_time).getTime() - new Date(right.start_time).getTime())
    .map((shift) => {
      const booked = bookings.filter((booking) => booking.shift_id === shift.shift_id && ACTIVE.has(booking.state));
      return {
        shift,
        names: booked.map((booking) => workers[booking.worker_id]?.display_name ?? "Booked worker"),
        codes: booked.map((booking) => (booking.state === "confirmed" ? booking.check_in_code ?? "" : "")),
        missing: Math.max(shift.workers_needed - booked.length, 0),
      };
    });
}

export function completedCounts(bookings: Booking[]) {
  const counts: Record<string, number> = {};
  for (const booking of bookings) {
    if (COMPLETED.has(booking.state)) counts[booking.worker_id] = (counts[booking.worker_id] ?? 0) + 1;
  }
  return counts;
}

export function regulars(bookings: Booking[], workers: Record<string, WorkerProfile>): Regular[] {
  const counts = completedCounts(bookings);
  return Object.entries(counts)
    .filter(([, completed]) => completed >= 3)
    .map(([workerId, completed]) => ({ worker: workers[workerId], completed }))
    .filter((entry): entry is Regular => Boolean(entry.worker))
    .sort((left, right) => right.completed - left.completed);
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
