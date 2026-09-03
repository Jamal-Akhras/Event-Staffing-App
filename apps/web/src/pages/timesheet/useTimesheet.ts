import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { downloadFile, fetchJson, postJson } from "../../lib/api";
import type { ApprovalResult, ApprovalRow, ChargeCorrection, TimesheetWeek } from "../../types/rota";

type Notify = (type: "success" | "error", message: string) => void;

export function useTimesheet(weekStart: string, notify: Notify) {
  const client = useQueryClient();

  const week = useQuery({
    queryKey: ["timesheet", weekStart],
    queryFn: () => fetchJson<TimesheetWeek>(`/venues/me/timesheet?week_start=${weekStart}`),
  });

  const settle = async () => {
    await Promise.all(
      ["timesheet", "bookings"].map((key) => client.invalidateQueries({ queryKey: [key] }))
    );
  };
  const fail = (error: Error) => notify("error", error.message);

  const approve = useMutation({
    mutationFn: (bookingIds: string[]) =>
      postJson<{ results: ApprovalRow[] }>("/venues/me/timesheet/approve", {
        booking_ids: bookingIds,
        now: new Date().toISOString(),
      }),
    onSuccess: async ({ results }) => {
      await settle();
      const approved = countOf(results, "approved");
      notify(approved > 0 ? "success" : "error", summarize(results));
    },
    onError: fail,
  });

  const adjust = useMutation({
    mutationFn: (input: { bookingId: string; checkedIn: string; checkedOut: string; reason: string }) =>
      postJson(`/venues/me/timesheet/bookings/${input.bookingId}/adjust`, {
        checked_in_at: input.checkedIn,
        checked_out_at: input.checkedOut,
        reason: input.reason,
        now: new Date().toISOString(),
      }),
    onSuccess: async () => {
      await settle();
      notify("success", "Hours adjusted — the original clock times are kept.");
    },
    onError: fail,
  });

  const recordAttendance = useMutation({
    mutationFn: (input: { bookingId: string; checkedIn: string; checkedOut: string }) =>
      postJson(`/venues/me/timesheet/bookings/${input.bookingId}/attendance`, {
        checked_in_at: input.checkedIn,
        checked_out_at: input.checkedOut,
        now: new Date().toISOString(),
      }),
    onSuccess: async () => {
      await settle();
      notify("success", "Attendance recorded.");
    },
    onError: fail,
  });

  const correct = useMutation({
    mutationFn: (input: { chargeId: string; deltaHours: string; reason: string }) =>
      postJson<ChargeCorrection>(`/venues/me/timesheet/charges/${input.chargeId}/correct`, {
        delta_hours: input.deltaHours,
        reason: input.reason,
        now: new Date().toISOString(),
      }),
    onSuccess: async () => {
      await settle();
      notify("success", "Correction recorded as its own line — the original charge is untouched.");
    },
    onError: fail,
  });

  const download = async () => {
    try {
      await downloadFile(`/venues/me/timesheet.csv?week_start=${weekStart}`, `timesheet-${weekStart}.csv`);
    } catch (err) {
      notify("error", (err as Error).message);
    }
  };

  return { week, approve, adjust, recordAttendance, correct, download };
}

function countOf(rows: ApprovalRow[], result: ApprovalResult) {
  return rows.filter((row) => row.result === result).length;
}

function summarize(rows: ApprovalRow[]): string {
  const parts: string[] = [];
  const approved = countOf(rows, "approved");
  const codes = countOf(rows, "needs_worker_code");
  const notReady = countOf(rows, "not_approvable_state");
  const already = countOf(rows, "already_approved");
  const missing = countOf(rows, "not_found");
  if (approved) parts.push(`${approved} approved`);
  if (codes) parts.push(`${codes} need the worker's completion code`);
  if (notReady) parts.push(`${notReady} not ready to approve`);
  if (already) parts.push(`${already} already approved`);
  if (missing) parts.push(`${missing} not found`);
  return parts.join(" · ") || "Nothing to approve.";
}
