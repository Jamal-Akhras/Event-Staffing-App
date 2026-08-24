import type { Shift } from "../../types";

export type ShiftFilter = "all" | "today" | "weekend" | "highPay";

export const FILTERS: { key: ShiftFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "today", label: "Today" },
  { key: "weekend", label: "Weekend" },
  { key: "highPay", label: "High pay" },
];

const DEFAULT_HIGH_PAY_THRESHOLD = 30;

export function payRateValue(shift: Shift): number {
  return Number(shift.pay_rate);
}

export function getShiftStats(shift: Shift) {
  const startDate = new Date(shift.start_time);
  const endDate = new Date(shift.end_time);
  const durationHours = Math.max(
    Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60)),
    0
  );
  const totalPay = payRateValue(shift) * durationHours;
  const filled = shift.workers_filled ?? 0;
  const needed = shift.workers_needed ?? 1;
  const remaining = Math.max(needed - filled, 0);
  const capacityPct = needed > 0 ? Math.min((filled / needed) * 100, 100) : 0;
  return { capacityPct, durationHours, filled, needed, remaining, totalPay };
}

export function getShiftTags(shift: Shift, highPayThreshold?: number | null) {
  const startDate = new Date(shift.start_time);
  const daysUntilShift = getDaysUntil(startDate);
  const threshold = highPayThreshold ?? DEFAULT_HIGH_PAY_THRESHOLD;
  const tags: string[] = [];
  if (payRateValue(shift) >= threshold) tags.push("High pay");
  if (startDate.getDay() === 0 || startDate.getDay() === 6) tags.push("Weekend");
  if (daysUntilShift <= 2) tags.push("Soon");
  if (getShiftStats(shift).remaining <= 1) tags.push("Last spot");
  return tags.slice(0, 3);
}

export function formatShiftWindow(shift: Shift) {
  const startDate = new Date(shift.start_time);
  const endDate = new Date(shift.end_time);
  const date = startDate.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const start = startDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const end = endDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} / ${start} - ${end}`;
}

export function buildQuickApplyMessage(shift: Shift) {
  return `I can cover ${shift.role.toLowerCase()} at ${shift.location}.`;
}

function getDaysUntil(date: Date) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86400000);
}
