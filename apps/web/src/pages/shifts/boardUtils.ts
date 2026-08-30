import { toLocalInput } from "../../lib/localInput";
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

export function shiftsOn(day: Date, shifts: Shift[]) {
  return shifts
    .filter((shift) => sameDay(new Date(shift.start_time), day))
    .sort((left, right) => new Date(left.start_time).getTime() - new Date(right.start_time).getTime());
}

export function nextDay(day: Date) {
  const next = new Date(day);
  next.setDate(next.getDate() + 1);
  return next;
}

export function shiftsWithin(days: Date[], shifts: Shift[]) {
  return shifts.filter((shift) => days.some((day) => sameDay(day, new Date(shift.start_time))));
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
