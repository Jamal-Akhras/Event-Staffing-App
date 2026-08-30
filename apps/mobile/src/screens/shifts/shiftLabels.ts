import type { Booking, ShiftSummary } from "../../types";

const DAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export function venueName(shift?: ShiftSummary | null) {
  return shift?.venue_name ?? "Venue";
}

export function roleLine(shift?: ShiftSummary | null) {
  if (!shift) return "Shift";
  return shift.location ? `${shift.role} · ${shift.location}` : shift.role;
}

export function clock(value: string) {
  return new Date(value).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

export function hoursRange(start: string, end: string) {
  return `${clock(start)} – ${clock(end)}`;
}

export function workedHours(start: string, end: string) {
  return (new Date(end).getTime() - new Date(start).getTime()) / 3_600_000;
}

export function shiftValue(booking: Booking) {
  if (!booking.shift) return null;
  return workedHours(booking.start_time, booking.end_time) * Number(booking.shift.pay_rate);
}

export function dayLabel(value: string, now: Date) {
  const date = new Date(value);
  const days = Math.round((startOfDay(date).getTime() - startOfDay(now).getTime()) / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  if (days > 1 && days < 7) return DAY[date.getDay()];
  return date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

export function whenLine(value: string, now: Date) {
  return `${dayLabel(value, now)}, ${clock(value)}`;
}

export function monthLabel(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { month: "long", year: "numeric" });
}

export function countdown(start: string, now: Date) {
  const minutes = Math.round((new Date(start).getTime() - now.getTime()) / 60_000);
  if (minutes <= 0) return "Started";
  if (minutes < 60) return `Starts in ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `Starts in ${hours} ${hours === 1 ? "hour" : "hours"}`;
  return null;
}

function startOfDay(date: Date) {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy;
}
