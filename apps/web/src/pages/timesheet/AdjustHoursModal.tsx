import { FormEvent, useState } from "react";

import { toLocalInput } from "../../lib/localInput";
import type { TimesheetDay } from "../../types/rota";
import "../../components/Modal.css";

type AdjustHoursModalProps = {
  day: TimesheetDay;
  workerName: string;
  mode: "adjust" | "record";
  busy: boolean;
  onClose: () => void;
  onSubmit: (payload: { checkedIn: string; checkedOut: string; reason: string }) => void;
};

export function AdjustHoursModal({ day, workerName, mode, busy, onClose, onSubmit }: AdjustHoursModalProps) {
  const [checkedIn, setCheckedIn] = useState(toLocalInput(day.scheduled_start));
  const [checkedOut, setCheckedOut] = useState(toLocalInput(day.scheduled_end));
  const [reason, setReason] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      checkedIn: new Date(checkedIn).toISOString(),
      checkedOut: new Date(checkedOut).toISOString(),
      reason,
    });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card modal ts-modal" onClick={(event) => event.stopPropagation()}>
        <div className="panel-title">
          <h3>{mode === "adjust" ? "Adjust hours" : "Record attendance"} · {workerName}</h3>
          <button className="btn ghost compact" type="button" onClick={onClose}>Cancel</button>
        </div>
        <form className="form" onSubmit={submit}>
          <label>
            Arrived
            <input type="datetime-local" value={checkedIn} onChange={(event) => setCheckedIn(event.target.value)} required />
          </label>
          <label>
            Left
            <input type="datetime-local" value={checkedOut} onChange={(event) => setCheckedOut(event.target.value)} required />
          </label>
          {mode === "adjust" && (
            <label>
              Reason
              <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Why the clocked times are wrong" minLength={3} required />
            </label>
          )}
          <p className="ts-modal-hint">
            {mode === "adjust"
              ? "The clocked times stay on record — approval will use these instead."
              : "This marks the whole shift as worked with the times you enter."}
          </p>
          <button className="btn primary" type="submit" disabled={busy}>
            {busy ? "Saving..." : mode === "adjust" ? "Save adjusted hours" : "Record attendance"}
          </button>
        </form>
      </section>
    </div>
  );
}

type CorrectChargeModalProps = {
  day: TimesheetDay;
  workerName: string;
  busy: boolean;
  onClose: () => void;
  onSubmit: (payload: { deltaHours: string; reason: string }) => void;
};

export function CorrectChargeModal({ day, workerName, busy, onClose, onSubmit }: CorrectChargeModalProps) {
  const [deltaHours, setDeltaHours] = useState("");
  const [reason, setReason] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({ deltaHours, reason });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card modal ts-modal" onClick={(event) => event.stopPropagation()}>
        <div className="panel-title">
          <h3>Correct approved hours · {workerName}</h3>
          <button className="btn ghost compact" type="button" onClick={onClose}>Cancel</button>
        </div>
        <form className="form" onSubmit={submit}>
          <p className="ts-modal-hint">
            {day.approved_hours}h are approved. Enter the change, not the new total — wages follow the frozen rate automatically.
          </p>
          <label>
            Hours to add or remove
            <input
              type="number"
              step="0.25"
              min="-99.75"
              max="99.75"
              value={deltaHours}
              onChange={(event) => setDeltaHours(event.target.value)}
              placeholder="0.5 or -1"
              required
            />
          </label>
          <label>
            Reason
            <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Why the approved hours are wrong" minLength={3} required />
          </label>
          <button className="btn primary" type="submit" disabled={busy}>
            {busy ? "Saving..." : "Record correction"}
          </button>
        </form>
      </section>
    </div>
  );
}
