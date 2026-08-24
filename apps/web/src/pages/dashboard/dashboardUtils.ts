import type { Application, Shift } from "../../types/operations";

export type MetricIcon =
  | "schedule"
  | "workers"
  | "applications"
  | "analytics";

export type DashboardMetric = {
  label: string;
  value: string;
  note: string;
  icon: MetricIcon;
  tone?: "default" | "warning" | "success";
};

export type AttentionItem = {
  label: string;
  value: string;
  note: string;
  to: string;
  action: string;
  tone: "warning" | "success" | "default";
};

export type CoverageDay = {
  label: string;
  date: string;
  totalShifts: number;
  openSeats: number;
};

export function buildDashboardMetrics(
  shifts: Shift[],
  applications: Application[],
  now: Date
): DashboardMetric[] {
  const upcomingShifts = getUpcomingShifts(shifts, now);
  const openShifts = shifts.filter((shift) => shift.status === "open");
  const filledShifts = shifts.filter((shift) => shift.status === "filled");
  const pendingApplications = applications.filter((app) => app.status === "applied");
  const fillRate = shifts.length > 0 ? (filledShifts.length / shifts.length) * 100 : 0;

  return [
    {
      label: "Next 7 days",
      value: String(upcomingShifts.length),
      note: `${openShifts.length} shifts open`,
      icon: "schedule",
      tone: openShifts.length > 0 ? "warning" : "success",
    },
    {
      label: "Open seats",
      value: String(getOpenSeats(shifts)),
      note: "Workers still needed",
      icon: "workers",
      tone: getOpenSeats(shifts) > 0 ? "warning" : "success",
    },
    {
      label: "Pending reviews",
      value: String(pendingApplications.length),
      note: pendingApplications.length > 0 ? "Needs decision" : "No queue",
      icon: "applications",
      tone: pendingApplications.length > 0 ? "warning" : "success",
    },
    {
      label: "Fill rate",
      value: `${fillRate.toFixed(0)}%`,
      note: `${filledShifts.length} of ${shifts.length} filled`,
      icon: "analytics",
    },
  ];
}

export function buildAttentionQueue(
  shifts: Shift[],
  applications: Application[],
  now: Date
): AttentionItem[] {
  const urgentShifts = getUrgentShifts(shifts, now);
  const pendingApplications = applications.filter((app) => app.status === "applied");
  const openSeats = getOpenSeats(shifts);

  const items: AttentionItem[] = [
    {
      label: "Shifts starting soon",
      value: String(urgentShifts.length),
      note: "Open shifts inside 48 hours",
      to: "/app/shifts",
      action: "Review shifts",
      tone: urgentShifts.length > 0 ? "warning" : "success",
    },
    {
      label: "Applications waiting",
      value: String(pendingApplications.length),
      note: "Approve or reject qualified workers",
      to: "/app/applications",
      action: "Open queue",
      tone: pendingApplications.length > 0 ? "warning" : "success",
    },
    {
      label: "Seats left to fill",
      value: String(openSeats),
      note: "Across active shifts",
      to: "/app/schedule",
      action: "View schedule",
      tone: openSeats > 0 ? "warning" : "success",
    },
  ];

  return items;
}

export function buildCoverageDays(shifts: Shift[], now: Date): CoverageDay[] {
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(now);
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + index);
    const dayShifts = shifts.filter((shift) => isSameDay(new Date(shift.start_time), date));

    return {
      label: date.toLocaleDateString("en-US", { weekday: "short" }),
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      totalShifts: dayShifts.length,
      openSeats: getOpenSeats(dayShifts),
    };
  });
}

export function getRecentOpenShifts(shifts: Shift[], now: Date) {
  return shifts
    .filter((shift) => shift.status === "open" && new Date(shift.start_time) >= now)
    .sort((left, right) => (
      new Date(left.start_time).getTime() - new Date(right.start_time).getTime()
    ))
    .slice(0, 5);
}

export function formatShiftTime(value: string) {
  return new Date(value).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function getUpcomingShifts(shifts: Shift[], now: Date) {
  const weekAhead = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  return shifts.filter((shift) => {
    const startTime = new Date(shift.start_time);
    return startTime >= now && startTime <= weekAhead;
  });
}

function getUrgentShifts(shifts: Shift[], now: Date) {
  return shifts.filter((shift) => {
    const hoursUntil =
      (new Date(shift.start_time).getTime() - now.getTime()) / (1000 * 60 * 60);
    return shift.status === "open" && hoursUntil > 0 && hoursUntil < 48;
  });
}

function getOpenSeats(shifts: Shift[]) {
  return shifts.reduce(
    (sum, shift) => sum + Math.max(shift.workers_needed - shift.workers_filled, 0),
    0
  );
}

function isSameDay(left: Date, right: Date) {
  return left.toDateString() === right.toDateString();
}
