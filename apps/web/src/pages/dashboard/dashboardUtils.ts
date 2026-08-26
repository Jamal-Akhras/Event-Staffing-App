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

export function getOpenSeats(shifts: Shift[]) {
  return shifts.reduce(
    (sum, shift) => sum + Math.max(shift.workers_needed - shift.workers_filled, 0),
    0
  );
}

function getUpcomingShifts(shifts: Shift[], now: Date) {
  const weekAhead = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  return shifts.filter((shift) => {
    const startTime = new Date(shift.start_time);
    return startTime >= now && startTime <= weekAhead;
  });
}

function isSameDay(left: Date, right: Date) {
  return left.toDateString() === right.toDateString();
}
