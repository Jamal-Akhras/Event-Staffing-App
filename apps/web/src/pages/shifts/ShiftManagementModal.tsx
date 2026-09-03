import { FormEvent, useState } from "react";

import { ApiError, postJson, putJson } from "../../lib/api";
import { fromVenueInput, toVenueInput } from "../../lib/venueTime";
import type { Booking, Shift, WorkerProfile } from "../../types/operations";
import { BookedWorkers } from "./BookedWorkers";
import "../../components/Modal.css";
import "./ShiftManagementModal.css";

type ShiftManagementModalProps = {
  shift: Shift;
  timezone: string;
  bookings?: Booking[];
  workers?: Record<string, WorkerProfile>;
  onChanged?: () => Promise<void>;
  onClose: () => void;
  onSaved: (message: string) => Promise<void>;
};

export function ShiftManagementModal({ shift, timezone, bookings, workers, onChanged, onClose, onSaved }: ShiftManagementModalProps) {
  const [form, setForm] = useState(() => ({
    role: shift.role,
    location: shift.location,
    start_time: toVenueInput(shift.start_time, timezone),
    end_time: toVenueInput(shift.end_time, timezone),
    pay_rate: String(shift.pay_rate),
    workers_needed: String(shift.workers_needed),
    notes: shift.notes ?? "",
  }));
  const [cancellationReason, setCancellationReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canManage = shift.status === "open" || shift.status === "filled";

  async function save(event: FormEvent) {
    event.preventDefault();
    await run("save", async () => {
      await putJson(`/shifts/${shift.shift_id}`, {
        role: form.role,
        location: form.location,
        start_time: fromVenueInput(form.start_time, timezone),
        end_time: fromVenueInput(form.end_time, timezone),
        pay_rate: Number(form.pay_rate),
        workers_needed: Number(form.workers_needed),
        notes: form.notes || null,
        now: new Date().toISOString(),
      });
      await onSaved("Shift updated.");
    });
  }

  async function advance(target: "pool" | "market") {
    await run(target, async () => {
      await postJson(`/shifts/${shift.shift_id}/advance`, { target, now: new Date().toISOString() });
      await onSaved(target === "pool" ? "Shift offered to your people." : "Shift published to the open market.");
    });
  }

  async function closeApplications() {
    if (!window.confirm("Close this shift to new applications? Confirmed workers will keep their bookings.")) return;
    await run("close", async () => {
      await postJson(`/shifts/${shift.shift_id}/close`, { now: new Date().toISOString() });
      await onSaved("Shift closed to new applications.");
    });
  }

  async function cancelShift() {
    if (cancellationReason.trim().length < 3) {
      setError("Give workers a short reason for the cancellation.");
      return;
    }
    if (!window.confirm(`Cancel this shift and ${shift.workers_filled} confirmed booking(s)?`)) return;
    await run("cancel", async () => {
      await postJson(`/shifts/${shift.shift_id}/cancel`, {
        reason: cancellationReason.trim(),
        now: new Date().toISOString(),
      });
      await onSaved("Shift cancelled and affected workers notified.");
    });
  }

  async function run(action: string, task: () => Promise<void>) {
    setBusy(action);
    setError(null);
    try {
      await task();
    } catch (err) {
      setError(err instanceof ApiError ? err.serverDetail ?? err.message : (err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card modal shift-management-modal" onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <div>
            <p className="management-eyebrow">Shift controls</p>
            <h2>{shift.role}</h2>
            <p className="booking-meta">{shift.workers_filled} of {shift.workers_needed} workers booked</p>
          </div>
          <button className="btn ghost" type="button" onClick={onClose}>Close</button>
        </header>

        {bookings && onChanged && (
          <BookedWorkers
            shift={shift}
            bookings={bookings.filter((booking) => booking.shift_id === shift.shift_id)}
            workers={workers ?? {}}
            onChanged={onChanged}
          />
        )}

        {canManage ? (
          <form className="shift-management-body" onSubmit={save}>
            <div className="shift-management-grid">
              <Field label="Role" value={form.role} onChange={(role) => setForm({ ...form, role })} />
              <Field label="Location" value={form.location} onChange={(location) => setForm({ ...form, location })} />
              <Field label="Start" type="datetime-local" value={form.start_time} onChange={(start_time) => setForm({ ...form, start_time })} />
              <Field label="End" type="datetime-local" value={form.end_time} onChange={(end_time) => setForm({ ...form, end_time })} />
              <Field label="Hourly pay" type="number" value={form.pay_rate} onChange={(pay_rate) => setForm({ ...form, pay_rate })} />
              <Field label="Workers needed" type="number" value={form.workers_needed} onChange={(workers_needed) => setForm({ ...form, workers_needed })} />
            </div>
            <label className="management-field">
              Notes
              <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} rows={3} />
            </label>
            <p className="management-hint">
              Once someone is booked, role, location, time and pay are locked. Notes and capacity can still change.
            </p>
            {error && <p className="status error">{error}</p>}
            <button className="btn primary" disabled={busy !== null} type="submit">
              {busy === "save" ? "Saving..." : "Save changes"}
            </button>

            <div className="management-divider" />
            {shift.origin && shift.origin !== "market" && (
              <section className="management-action-row">
                <div>
                  <strong>{shift.origin === "assigned" ? "Assigned to one person" : "With your people"}</strong>
                  <p>
                    {shift.origin === "assigned"
                      ? "Only the assigned worker can see this shift. Widen it without waiting for the timer."
                      : "Only your team and pool can see this shift. Publish it to the open market now."}
                  </p>
                </div>
                <span className="st-inline">
                  {shift.origin === "assigned" && (
                    <button className="btn secondary" disabled={busy !== null} type="button" onClick={() => advance("pool")}>
                      {busy === "pool" ? "Offering..." : "Offer to your people"}
                    </button>
                  )}
                  <button className="btn secondary" disabled={busy !== null} type="button" onClick={() => advance("market")}>
                    {busy === "market" ? "Publishing..." : "Publish to market"}
                  </button>
                </span>
              </section>
            )}

            <section className="management-action-row">
              <div>
                <strong>Close applications</strong>
                <p>Reject pending applicants while keeping confirmed workers scheduled.</p>
              </div>
              <button className="btn secondary" disabled={busy !== null} type="button" onClick={closeApplications}>
                {busy === "close" ? "Closing..." : "Close shift"}
              </button>
            </section>

            <section className="management-danger-zone">
              <div>
                <strong>Cancel the entire shift</strong>
                <p>This cancels {shift.workers_filled} confirmed booking(s) and notifies every affected worker.</p>
              </div>
              <textarea
                value={cancellationReason}
                onChange={(event) => setCancellationReason(event.target.value)}
                placeholder="Tell workers why the shift is being cancelled"
                rows={3}
              />
              <button className="btn danger" disabled={busy !== null} type="button" onClick={cancelShift}>
                {busy === "cancel" ? "Cancelling..." : "Cancel shift"}
              </button>
            </section>
          </form>
        ) : (
          <div className="shift-management-body">
            <p className="booking-meta">This shift is {shift.status} and is retained as an operational record.</p>
            {shift.cancellation_reason && <p className="management-reason">{shift.cancellation_reason}</p>}
          </div>
        )}
      </section>
    </div>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="management-field">
      {label}
      <input type={type} value={value} min={type === "number" ? "0" : undefined} step={label === "Hourly pay" ? "0.01" : undefined} onChange={(event) => onChange(event.target.value)} required />
    </label>
  );
}
