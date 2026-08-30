import type { Shift } from "./operations";

export type DayCoverage = {
  day: string;
  total_shifts: number;
  open_seats: number;
};

export type PendingApplications = {
  count: number;
  oldest_created_at: string | null;
};

export type Attendance = {
  completed: number;
  no_shows: number;
  total: number;
  rate: number | null;
};

export type TonightWorker = {
  booking_id: string;
  worker_id: string;
  state: string;
  check_in_code: string | null;
};

export type TonightShift = {
  shift: Shift;
  workers: TonightWorker[];
  missing: number;
};

export type VenueOverview = {
  window_start: string;
  days: DayCoverage[];
  open_seats: number;
  pending_applications: PendingApplications;
  attendance: Attendance;
  tonight: TonightShift[];
};

export type WorkerActivity = {
  worker_id: string;
  completed: number;
  last_worked: string | null;
  recently_broken: boolean;
};

export type RosterActivity = {
  workers: WorkerActivity[];
};

export type AnalyticsGap = {
  shift_id: string;
  role: string;
  location: string;
  start_time: string;
  unfilled: number;
  applications: number;
  lead_time_hours: number;
  pay_rate: string;
  reason: string;
};

export type AnalyticsRole = { role: string; seats: number };

export type VenueAnalytics = {
  period: string;
  window_start: string;
  window_end: string;
  seats_posted: number;
  seats_filled: number;
  fill_rate: number;
  applications: number;
  applications_per_seat: number;
  hours_staffed: string;
  average_pay_rate: string;
  currency: string;
  fill_rate_trend: number[];
  applications_trend: number[];
  hours_trend: number[];
  rate_trend: number[];
  gaps: AnalyticsGap[];
  roles: AnalyticsRole[];
};

export type AnalyticsPeriod = "week" | "month" | "quarter";
