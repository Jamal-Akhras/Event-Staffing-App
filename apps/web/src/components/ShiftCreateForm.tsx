import { FormEvent, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { postJson } from "../lib/api";
import { addHours } from "../lib/localInput";
import "./ShiftCreateForm.css";

const CURRENCY_SYMBOL: Record<string, string> = {
  GBP: "£",
  AED: "د.إ",
  USD: "$",
  EUR: "€",
};

export type ShiftDraft = {
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: string;
  workers_needed: string;
  notes: string;
};

type ShiftCreateFormProps = {
  initial?: Partial<ShiftDraft>;
  durationHours?: number;
  onCreated: () => Promise<void>;
  onError: (message: string) => void;
  onCancel?: () => void;
};

export function ShiftCreateForm({ initial, durationHours, onCreated, onError, onCancel }: ShiftCreateFormProps) {
  const { user } = useAuth();
  const currency = user?.currency ?? "GBP";
  const symbol = CURRENCY_SYMBOL[currency] ?? currency;
  const [form, setForm] = useState<ShiftDraft>({
    role: "",
    location: "",
    start_time: "",
    end_time: "",
    pay_rate: "",
    workers_needed: "1",
    notes: "",
    ...initial,
  });
  const [saving, setSaving] = useState(false);

  const update = (patch: Partial<ShiftDraft>) => setForm((current) => ({ ...current, ...patch }));

  const setStart = (start_time: string) => {
    const end_time = durationHours && start_time ? addHours(start_time, durationHours) : form.end_time;
    update({ start_time, end_time });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await postJson("/shifts", {
        role: form.role,
        location: form.location,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
        pay_rate: Number(form.pay_rate),
        workers_needed: Number(form.workers_needed),
        notes: form.notes || null,
        now: new Date().toISOString(),
      });
      await onCreated();
    } catch (err) {
      onError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const stepWorkers = (delta: number) => {
    const current = Number(form.workers_needed) || 1;
    update({ workers_needed: String(Math.max(current + delta, 1)) });
  };

  return (
    <div className="panel">
      <div className="panel-title">
        <h3>Post a shift</h3>
        {onCancel && (
          <button className="btn ghost compact" type="button" onClick={onCancel}>Cancel</button>
        )}
      </div>
      <form className="form" onSubmit={submit}>
        <label>
          Role
          <input value={form.role} onChange={(event) => update({ role: event.target.value })} placeholder="Bartender, Server, Host" required />
        </label>
        <label>
          Location
          <input value={form.location} onChange={(event) => update({ location: event.target.value })} placeholder="Main bar, terrace, function room" required />
        </label>
        <label>
          Start
          <input type="datetime-local" value={form.start_time} onChange={(event) => setStart(event.target.value)} required />
        </label>
        <label>
          End
          <input type="datetime-local" value={form.end_time} onChange={(event) => update({ end_time: event.target.value })} required />
        </label>
        <label>
          Pay rate ({symbol}/hr)
          <input type="number" value={form.pay_rate} onChange={(event) => update({ pay_rate: event.target.value })} placeholder="14.50" min="0" step="0.01" required />
        </label>
        <label>
          Workers needed
          <div className="stepper-control">
            <button type="button" className="btn ghost stepper-button" onClick={() => stepWorkers(-1)}>-</button>
            <input type="number" value={form.workers_needed} onChange={(event) => update({ workers_needed: event.target.value })} min="1" className="stepper-input" required />
            <button type="button" className="btn ghost stepper-button" onClick={() => stepWorkers(1)}>+</button>
          </div>
        </label>
        <label>
          Notes (optional)
          <input value={form.notes} onChange={(event) => update({ notes: event.target.value })} placeholder="Dress code, arrival details, requirements" />
        </label>
        <button className="btn primary" type="submit" disabled={saving}>
          {saving ? "Posting..." : "Post shift"}
        </button>
      </form>
    </div>
  );
}
