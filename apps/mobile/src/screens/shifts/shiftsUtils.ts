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

export function sortHighlightedFirst<T>(
  items: T[],
  highlightedId: string | null | undefined,
  getId: (item: T) => string
): T[] {
  return [...items].sort(
    (left, right) =>
      Number(getId(right) === highlightedId) - Number(getId(left) === highlightedId)
  );
}

export function formatDateTime(value?: string | null) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function getCheckInWindow(booking: Booking | null) {
  if (!booking) return "N/A";
  const start = new Date(booking.start_time);
  if (Number.isNaN(start.getTime())) return "N/A";
  const open = new Date(start.getTime() - 30 * 60 * 1000);
  const close = new Date(start.getTime() + 15 * 60 * 1000);
  return `${open.toLocaleTimeString()} - ${close.toLocaleTimeString()}`;
}
