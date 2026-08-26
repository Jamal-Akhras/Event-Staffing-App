import { useState } from "react";

import { useToast } from "../../components/Toast";
import { ApiError, postJson } from "../../lib/api";
import type { Booking, Shift, WorkerProfile } from "../../types/operations";
import { clock } from "../dashboard/dashboardUtils";
import "./BookedWorkers.css";

const PAYMENT_METHODS = [
  ["bank_transfer", "Bank transfer"],
  ["cash", "Cash"],
  ["payroll", "Payroll"],
  ["other", "Other"],
] as const;

const STATE_LABELS: Record<string, string> = {
  requested: "Requested",
  confirmed: "Booked",
  checked_in: "Checked in",
  checked_out: "Finished · hours to approve",
  approved: "Hours approved · pay the worker",
  paid: "Paid",
  no_show: "No-show",
  cancelled_by_worker: "Cancelled by worker",
  cancelled_by_operator: "Cancelled by you",
};

type BookedWorkersProps = {
  shift: Shift;
  bookings: Booking[];
  workers: Record<string, WorkerProfile>;
  onChanged: () => Promise<void>;
};

export function BookedWorkers({ shift, bookings, workers, onChanged }: BookedWorkersProps) {
  const { toast } = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const [codes, setCodes] = useState<Record<string, string>>({});
  const [methods, setMethods] = useState<Record<string, string>>({});
  const [references, setReferences] = useState<Record<string, string>>({});
  const lateAfter = new Date(shift.start_time).getTime() + 15 * 60_000;

  const act = async (booking: Booking, action: string, body: object, success: string) => {
    setBusy(booking.booking_id);
    try {
      await postJson(`/bookings/${booking.booking_id}/${action}`, { ...body, now: new Date().toISOString() });
      await onChanged();
      toast({ type: "success", message: success });
    } catch (err) {
      toast({ type: "error", message: err instanceof ApiError ? err.serverDetail ?? err.message : (err as Error).message });
    } finally {
      setBusy(null);
    }
  };

  if (!bookings.length) {
    return <section className="bw"><p className="bw-empty">Nobody is booked on this shift yet.</p></section>;
  }

  return (
    <section className="bw">
      <h3 className="bw-title">Booked workers</h3>
      {bookings.map((booking) => {
        const name = workers[booking.worker_id]?.display_name || "Worker";
        const code = codes[booking.booking_id] ?? "";
        const method = methods[booking.booking_id] ?? "bank_transfer";
        const reference = references[booking.booking_id] ?? "";
        const disabled = busy !== null;
        const late = booking.state === "confirmed" && Date.now() > lateAfter;
        return (
          <div key={booking.booking_id} className="bw-row">
            <div className="bw-who">
              <b>{name}</b>
              <span>
                {STATE_LABELS[booking.state] ?? booking.state}
                {booking.checked_in_at ? ` · in ${clock(booking.checked_in_at)}` : ""}
                {booking.checked_out_at ? ` · out ${clock(booking.checked_out_at)}` : ""}
              </span>
            </div>
            <div className="bw-actions">
              {(booking.state === "confirmed" || booking.state === "checked_in") && booking.check_in_code && (
                <span className="bw-code" title="The worker types this code to check in">
                  Check-in code <b>{booking.check_in_code}</b>
                </span>
              )}
              {booking.state === "checked_out" && (
                <>
                  <input
                    className="bw-input bw-input-code"
                    inputMode="numeric"
                    maxLength={4}
                    placeholder="Worker's code"
                    value={code}
                    onChange={(event) => setCodes({ ...codes, [booking.booking_id]: event.target.value.replace(/\D/g, "") })}
                  />
                  <button type="button" className="btn primary compact" disabled={disabled || code.length !== 4} onClick={() => act(booking, "approve", { code }, `${name}'s hours approved.`)}>
                    Approve hours
                  </button>
                </>
              )}
              {booking.state === "approved" && (
                <>
                  <select className="bw-input" value={method} onChange={(event) => setMethods({ ...methods, [booking.booking_id]: event.target.value })}>
                    {PAYMENT_METHODS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                  <input className="bw-input" placeholder="Reference (optional)" value={reference} onChange={(event) => setReferences({ ...references, [booking.booking_id]: event.target.value })} />
                  <button type="button" className="btn primary compact" disabled={disabled} onClick={() => act(booking, "record-payment", { confirmation: "PAYMENT_SENT", method, reference: reference || null }, `Payment to ${name} recorded.`)}>
                    Record payment
                  </button>
                </>
              )}
              {booking.state === "paid" && <span className="bw-paid">Paid · {booking.payment_method?.replace("_", " ")}</span>}
              {late && (
                <button type="button" className="btn ghost compact" disabled={disabled} onClick={() => window.confirm(`Mark ${name} as a no-show?`) && act(booking, "no-show", {}, `${name} marked as a no-show.`)}>
                  Mark no-show
                </button>
              )}
            </div>
          </div>
        );
      })}
    </section>
  );
}
