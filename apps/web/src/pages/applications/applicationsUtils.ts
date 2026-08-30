import type { RailEvent } from "../../components/WorkerRail";
import type { Application, Booking, Shift, WorkerProfile } from "../../types/operations";
import { relativeTime, shortDay } from "../dashboard/dashboardUtils";

const COMPLETED = new Set(["checked_out", "approved", "paid"]);

export type Applicant = {
  application: Application;
  worker?: WorkerProfile;
  workedHere: number;
};

export type ShiftGroup = {
  shift: Shift;
  openSeats: number;
  urgent: boolean;
  applicants: Applicant[];
};

export type Evidence = {
  reliability: string;
  tone: "good" | "fair" | "poor" | "unknown";
  history: string;
  applied: string;
};

export function buildGroups(
  applications: Application[],
  shifts: Shift[],
  workers: Record<string, WorkerProfile>,
  workedCounts: Record<string, number>,
  now: Date
): ShiftGroup[] {
  const shiftsById = Object.fromEntries(shifts.map((shift) => [shift.shift_id, shift]));
  const byShift = new Map<string, Applicant[]>();
  for (const application of applications) {
    if (!shiftsById[application.shift_id]) continue;
    const applicant: Applicant = {
      application,
      worker: workers[application.worker_id],
      workedHere: workedCounts[application.worker_id] ?? 0,
    };
    byShift.set(application.shift_id, [...(byShift.get(application.shift_id) ?? []), applicant]);
  }

  return Array.from(byShift.entries())
    .map(([shiftId, applicants]) => {
      const shift = shiftsById[shiftId];
      const openSeats = Math.max(shift.workers_needed - shift.workers_filled, 0);
      const hoursAway = (new Date(shift.start_time).getTime() - now.getTime()) / 3_600_000;
      return {
        shift,
        openSeats,
        urgent: openSeats > 0 && hoursAway <= 48,
        applicants: applicants.sort(rankApplicants),
      };
    })
    .sort((left, right) => new Date(left.shift.start_time).getTime() - new Date(right.shift.start_time).getTime());
}

function rankApplicants(left: Applicant, right: Applicant) {
  if (left.workedHere !== right.workedHere) return right.workedHere - left.workedHere;
  const leftScore = left.worker?.reliability_score ?? 0;
  const rightScore = right.worker?.reliability_score ?? 0;
  if (leftScore !== rightScore) return rightScore - leftScore;
  return new Date(left.application.created_at).getTime() - new Date(right.application.created_at).getTime();
}

export function evidenceFor(applicant: Applicant, now: Date): Evidence {
  const score = applicant.worker?.reliability_score ?? 0;
  const percent = Math.round(score * 100);
  return {
    reliability: score > 0 ? `${percent}% reliability` : "No history yet",
    tone: score === 0 ? "unknown" : percent >= 90 ? "good" : percent >= 80 ? "fair" : "poor",
    history: applicant.workedHere > 0 ? `worked here ${applicant.workedHere}×` : "new to you",
    applied: `applied ${relativeTime(new Date(applicant.application.created_at), now)}`,
  };
}

export function completedBookings(bookings: Booking[], workerId: string) {
  return bookings
    .filter((booking) => booking.worker_id === workerId && COMPLETED.has(booking.state))
    .sort((left, right) => new Date(right.start_time).getTime() - new Date(left.start_time).getTime());
}

export function workerHistory(bookings: Booking[], shifts: Shift[], workerId: string): RailEvent[] {
  const shiftsById = Object.fromEntries(shifts.map((shift) => [shift.shift_id, shift]));
  return completedBookings(bookings, workerId)
    .slice(0, 4)
    .map((booking) => {
      const shift = shiftsById[booking.shift_id];
      return {
        label: shift ? `${shift.role} · ${shift.location}` : "Shift",
        when: shortDay(booking.start_time),
      };
    });
}

export function lastWorkedLabel(bookings: Booking[], workerId: string) {
  const [latest] = completedBookings(bookings, workerId);
  return latest ? shortDay(latest.start_time) : "Never";
}

export function statusLabel(application: Application, booking?: Booking) {
  if (application.status !== "approved") return application.status === "withdrawn" ? "Withdrawn" : "Declined";
  if (!booking) return "Booked";
  const labels: Record<string, string> = {
    confirmed: "Booked",
    checked_in: "Checked in",
    checked_out: "Finished",
    approved: "Hours approved",
    paid: "Paid",
    no_show: "No-show",
    cancelled_by_worker: "Cancelled by worker",
    cancelled_by_operator: "Cancelled by you",
  };
  return labels[booking.state] ?? booking.state;
}
