import { toLocalInput } from "../../lib/localInput";
import { toVenueWallDate } from "../../lib/venueTime";
import type { Application, Shift } from "../../types/operations";

export function startOfDay(date: Date) {
  const start = new Date(date);
  start.setHours(0, 0, 0, 0);
  return start;
}

export function shiftDays(start: Date, days: number) {
  const next = new Date(start);
  next.setDate(next.getDate() + days);
  return next;
}

export function weekStartFor(date: Date, weekStart: number) {
  const day = startOfDay(date);
  return shiftDays(day, -((day.getDay() - weekStart + 7) % 7));
}

export function boardDays(start: Date) {
  return Array.from({ length: 7 }, (_, index) => shiftDays(start, index));
}

export function boardLabel(days: Date[]) {
  const first = days[0];
  const last = days[days.length - 1];
  const month = (date: Date) => date.toLocaleDateString("en-GB", { month: "long" });
  if (first.getMonth() === last.getMonth()) {
    return `${first.getDate()} – ${last.getDate()} ${month(first)}`;
  }
  return `${first.getDate()} ${month(first)} – ${last.getDate()} ${month(last)}`;
}

export function sameDay(left: Date, right: Date) {
  return left.toDateString() === right.toDateString();
}

export function shiftsOn(day: Date, shifts: Shift[], timezone: string) {
  return shifts
    .filter((shift) => sameDay(toVenueWallDate(shift.start_time, timezone), day))
    .sort((left, right) => new Date(left.start_time).getTime() - new Date(right.start_time).getTime());
}

export function nextDay(day: Date) {
  const next = new Date(day);
  next.setDate(next.getDate() + 1);
  return next;
}

export function shiftsWithin(days: Date[], shifts: Shift[], timezone: string) {
  return shifts.filter((shift) =>
    days.some((day) => sameDay(day, toVenueWallDate(shift.start_time, timezone)))
  );
}

export function missingSeats(shift: Shift) {
  return shift.status === "open" ? Math.max(shift.workers_needed - shift.workers_filled, 0) : 0;
}

export function appliedCount(shiftId: string, applications: Application[]) {
  return applications.filter((application) => application.shift_id === shiftId && application.status === "applied").length;
}

export function defaultStartFor(day: Date) {
  const start = new Date(day);
  start.setHours(18, 0, 0, 0);
  return toLocalInput(start);
}

export function isoDay(date: Date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export function shiftHours(shift: Shift) {
  return (new Date(shift.end_time).getTime() - new Date(shift.start_time).getTime()) / 3_600_000;
}

export function isCostable(shift: Shift) {
  return shift.status !== "cancelled" && shift.status !== "closed";
}

export function projectedCost(shifts: Shift[]) {
  return shifts
    .filter(isCostable)
    .reduce((sum, shift) => sum + shiftHours(shift) * Number(shift.pay_rate) * shift.workers_needed, 0);
}

export function seatsOn(shifts: Shift[]) {
  return shifts.filter(isCostable).reduce((sum, shift) => sum + shift.workers_needed, 0);
}

export function roleCosts(shifts: Shift[]) {
  const rollup = new Map<string, { role: string; hours: number; cost: number }>();
  for (const shift of shifts.filter(isCostable)) {
    const entry = rollup.get(shift.role) ?? { role: shift.role, hours: 0, cost: 0 };
    entry.hours += shiftHours(shift) * shift.workers_needed;
    entry.cost += shiftHours(shift) * Number(shift.pay_rate) * shift.workers_needed;
    rollup.set(shift.role, entry);
  }
  return [...rollup.values()].sort((left, right) => right.cost - left.cost);
}

export function scheduledHoursByWorker(shifts: Shift[]) {
  const hours = new Map<string, number>();
  for (const shift of shifts.filter(isCostable)) {
    if (!shift.assigned_worker_id) continue;
    hours.set(shift.assigned_worker_id, (hours.get(shift.assigned_worker_id) ?? 0) + shiftHours(shift));
  }
  return hours;
}
