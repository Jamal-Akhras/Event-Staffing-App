export type RotaChangeKind = "added" | "removed" | "reassigned" | "time_changed";

export type RotaChange = {
  kind: RotaChangeKind;
  shift_id: string;
  role: string;
  worker_id?: string | null;
  previous_worker_id?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  previous_start_time?: string | null;
  previous_end_time?: string | null;
};

export type RotaAssignment = {
  shift_id: string;
  worker_id: string;
  role: string;
  start_time: string;
  end_time: string;
};

export type RotaPublication = {
  publication_id: string;
  venue_id: string;
  week_start: string;
  revision: number;
  published_at: string;
  published_by_user_id: string;
  assignments: RotaAssignment[];
  changes: RotaChange[];
};

export type RotaPublishResult = {
  publication: RotaPublication;
  booked_worker_ids: string[];
  offered_worker_ids: string[];
};

export type TimesheetDay = {
  day: string;
  booking_id: string;
  charge_id: string | null;
  shift_id: string;
  role: string;
  state: string;
  attendance_mode: "pin" | "employed";
  scheduled_start: string;
  scheduled_end: string;
  scheduled_hours: string;
  worked_hours: string | null;
  hours_source: "clocked" | "adjusted" | "venue_recorded" | "scheduled" | "approved";
  approved_hours: string | null;
  approved_wages: string | null;
  adjustments_total_hours: string;
};

export type TimesheetWorker = {
  worker_id: string;
  display_name: string;
  relationship_type: string;
  contracted_hours_per_week: string | null;
  scheduled_hours: string;
  worked_hours: string;
  approved_hours: string;
  days: TimesheetDay[];
};

export type TimesheetWeek = {
  venue_id: string;
  week_start: string;
  workers: TimesheetWorker[];
  total_scheduled_hours: string;
  total_worked_hours: string;
  total_approved_hours: string;
  total_approved_wages: string;
};

export type ApprovalResult =
  | "approved"
  | "needs_worker_code"
  | "not_approvable_state"
  | "not_found"
  | "already_approved";

export type ApprovalRow = {
  booking_id: string;
  result: ApprovalResult;
};

export type ChargeCorrection = {
  adjustment_id: string;
  charge_id: string;
  booking_id: string;
  delta_hours: string;
  delta_wages: string;
  delta_fee: string;
  reason: string;
  created_at: string;
};
