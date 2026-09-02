import { formatClock, formatDayDate } from "../../lib/format";
import type { Booking } from "../../types";

export type ShiftTab = "upcoming" | "previous" | "applications";

export const SHIFT_TABS: { key: ShiftTab; label: string }[] = [
  { key: "upcoming", label: "Upcoming" },
  { key: "previous", label: "Previous" },
  { key: "applications", label: "Applications" },
];

export function getUpcomingBookings(bookings: Booking[]) {
  const now = Date.now();
  return bookings.filter((booking) => {
    const end = new Date(booking.end_time).getTime();
    return (
      end >= now &&
      booking.state !== "cancelled_by_worker" &&
      booking.state !== "cancelled_by_operator"
    );
  });
}

export function getPreviousBookings(bookings: Booking[]) {
  const now = Date.now();
  return bookings.filter((booking) => {
    const end = new Date(booking.end_time).getTime();
    return end < now || booking.state === "no_show" || booking.state.startsWith("cancelled");
  });
}

export function formatDateTime(value?: string | null) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${formatDayDate(date)}, ${formatClock(date)}`;
}

export function getCheckInWindow(booking: Booking | null) {
  if (!booking) return "N/A";
  const start = new Date(booking.start_time);
  if (Number.isNaN(start.getTime())) return "N/A";
  const open = new Date(start.getTime() - 30 * 60 * 1000);
  const close = new Date(start.getTime() + 15 * 60 * 1000);
  return `${formatClock(open)} - ${formatClock(close)}`;
}

export function groupByMonth(bookings: Booking[]): { month: string; items: Booking[] }[] {
  const groups = new Map<string, Booking[]>();
  const ordered = [...bookings].sort(
    (left, right) => new Date(right.start_time).getTime() - new Date(left.start_time).getTime()
  );
  for (const booking of ordered) {
    const key = new Date(booking.start_time).toLocaleDateString("en-GB", {
      month: "long",
      year: "numeric",
    });
    const existing = groups.get(key);
    if (existing) existing.push(booking);
    else groups.set(key, [booking]);
  }
  return [...groups.entries()].map(([month, items]) => ({ month, items }));
}

export function nextLiveBooking(bookings: Booking[]): Booking | null {
  const active = bookings
    .filter((booking) => booking.state === "confirmed" || booking.state === "checked_in")
    .sort((left, right) => new Date(left.start_time).getTime() - new Date(right.start_time).getTime());
  return active.find((booking) => booking.state === "checked_in") ?? active[0] ?? null;
}

export function awaitingRating(bookings: Booking[]): Booking[] {
  return bookings.filter((booking) => booking.state === "checked_out");
}
