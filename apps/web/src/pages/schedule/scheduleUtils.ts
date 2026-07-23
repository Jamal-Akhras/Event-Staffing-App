import type { Shift } from "../../types/operations";

export const DAYS_OF_WEEK = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

export function getWeekStart(date: Date) {
  const weekStart = new Date(date);
  weekStart.setHours(0, 0, 0, 0);
  weekStart.setDate(weekStart.getDate() - weekStart.getDay());
  return weekStart;
}

export function getWeekDates(currentWeekStart: Date) {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(currentWeekStart);
    date.setDate(date.getDate() + index);
    return date;
  });
}

export function groupShiftsByDay(shifts: Shift[], weekDates: Date[]) {
  return weekDates.map((date) => {
    const dateKey = formatDateKey(date);
    return shifts.filter((shift) => formatDateKey(new Date(shift.start_time)) === dateKey);
  });
}

export function getWeekLabel(currentWeekStart: Date) {
  const weekEndDate = new Date(currentWeekStart);
  weekEndDate.setDate(weekEndDate.getDate() + 6);
  return `${formatDate(currentWeekStart)} - ${formatDate(weekEndDate)}`;
}

export function getWeekSummary(shiftsByDay: Shift[][]) {
  const weekShifts = shiftsByDay.flat();
  return {
    total: weekShifts.length,
    open: weekShifts.filter((shift) => shift.status === "open").length,
    filled: weekShifts.filter((shift) => shift.status === "filled").length,
    seatsOpen: weekShifts.reduce(
      (sum, shift) => sum + Math.max(shift.workers_needed - shift.workers_filled, 0),
      0
    ),
  };
}

export function formatTime(value: string) {
  return new Date(value).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatLongDate(value: string) {
  return new Date(value).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDate(value: Date) {
  return value.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateKey(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
