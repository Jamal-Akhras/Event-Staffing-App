import { FormEvent, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { postJson } from "../lib/api";
import { addVenueHours, fromVenueInput } from "../lib/venueTime";
import { usePeople } from "../pages/workers/useDirectory";
import { RELATIONSHIP_LABELS } from "../types/workforce";
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
  assigned_worker_id: string;
  required_certification: string;
  risk_information: string;
};

type ShiftCreateFormProps = {
  initial?: Partial<ShiftDraft>;
  timezone: string;
  durationHours?: number;
  onCreated: () => Promise<void>;
  onError: (message: string) => void;
  onCancel?: () => void;
};

export function ShiftCreateForm({ initial, timezone, durationHours, onCreated, onError, onCancel }: ShiftCreateFormProps) {
  const { user } = useAuth();
  const people = usePeople();
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
    assigned_worker_id: "",
    required_certification: "",
    risk_information: "",
    ...initial,
  });
  const [saving, setSaving] = useState(false);

  const assignable = (people.data ?? []).filter(
    (entry) => entry.status === "active" && entry.relationship_type !== "one_off"
  );
  const assignee = assignable.find((entry) => entry.worker_id === form.assigned_worker_id) ?? null;
  const agreedRate = assignee?.agreed_rate ? Number(assignee.agreed_rate) : null;
  const rateMismatch =
    agreedRate !== null && form.pay_rate !== "" && Number(form.pay_rate) !== agreedRate;

  const update = (patch: Partial<ShiftDraft>) => setForm((current) => ({ ...current, ...patch }));

  const setStart = (start_time: string) => {
    const end_time = durationHours && start_time
      ? addVenueHours(start_time, durationHours, timezone)
      : form.end_time;
    update({ start_time, end_time });
  };

  const setAssignee = (assigned_worker_id: string) => {
    const entry = assignable.find((candidate) => candidate.worker_id === assigned_worker_id);
    const patch: Partial<ShiftDraft> = { assigned_worker_id };
    if (assigned_worker_id) {
      patch.workers_needed = "1";
      if (entry?.agreed_rate && form.pay_rate === "") patch.pay_rate = entry.agreed_rate;
      if (entry?.role && form.role === "") patch.role = entry.role;
    }
    update(patch);
  };

  const [drafting, setDrafting] = useState(false);

  const draftPost = async () => {
    if (!form.role || !form.location || !form.start_time || !form.end_time) {
      onError("Add role, location and times first, then I can draft it.");
      return;
    }
    setDrafting(true);
    try {
      const draft = await postJson<{
        description: string;
        suggested_pay_low: string | null;
        suggested_pay_high: string | null;
        pay_basis: string;
      }>("/assistant/shift-post", {
        role: form.role,
        location: form.location,
        start_time: fromVenueInput(form.start_time, timezone),
        end_time: fromVenueInput(form.end_time, timezone),
        pay_rate: form.pay_rate ? Number(form.pay_rate) : null,
        note: form.notes || null,
      });
      const patch: Partial<ShiftDraft> = { notes: draft.description };
      if (!form.pay_rate && draft.suggested_pay_low) patch.pay_rate = draft.suggested_pay_low;
      update(patch);
    } catch (err) {
      onError((err as Error).message);
    } finally {
      setDrafting(false);
    }
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await postJson("/shifts", {
        role: form.role,
        location: form.location,
        start_time: fromVenueInput(form.start_time, timezone),
        end_time: fromVenueInput(form.end_time, timezone),
        pay_rate: Number(form.pay_rate),
        workers_needed: form.assigned_worker_id ? 1 : Number(form.workers_needed),
        notes: form.notes || null,
        required_certification: form.required_certification.trim() || null,
        risk_information: form.risk_information.trim() || null,
        now: new Date().toISOString(),
        ...(form.assigned_worker_id
          ? { assigned_worker_id: form.assigned_worker_id, rota_state: "draft" }
          : {}),
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
        <h3>{form.assigned_worker_id ? "Add to the rota" : "Post a shift"}</h3>
        {onCancel && (
          <button className="btn ghost compact" type="button" onClick={onCancel}>Cancel</button>
        )}
      </div>
      <form className="form" onSubmit={submit}>
        {assignable.length > 0 && (
          <label>
            Assign to
            <select value={form.assigned_worker_id} onChange={(event) => setAssignee(event.target.value)}>
              <option value="">Open shift — anyone can apply</option>
              {assignable.map((entry) => (
                <option key={entry.worker_id} value={entry.worker_id}>
                  {entry.display_name} · {RELATIONSHIP_LABELS[entry.relationship_type]}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Role
          <input value={form.role} onChange={(event) => update({ role: event.target.value })} placeholder="Bartender, Server, Host" required />
        </label>
        <label>
          Requires certification
          <input
            value={form.required_certification}
            onChange={(event) => update({ required_certification: event.target.value })}
            placeholder="Optional — e.g. Personal Licence"
          />
        </label>
        <label>
          Risk information for workers
          <textarea
            value={form.risk_information}
            onChange={(event) => update({ risk_information: event.target.value })}
            placeholder="Hazards, safety gear, site notes — shown to the worker before they accept"
            rows={2}
          />
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
        {rateMismatch && assignee && (
          <p className="sc-hint">
            You agreed {symbol}{agreedRate?.toFixed(2)}/hr with {assignee.display_name} — this shift pays {symbol}{Number(form.pay_rate).toFixed(2)}.
          </p>
        )}
        {form.assigned_worker_id ? (
          <p className="sc-hint">Assigned shifts hold one seat. It stays a draft until you publish the week.</p>
        ) : (
          <label>
            Workers needed
            <div className="stepper-control">
              <button type="button" className="btn ghost stepper-button" onClick={() => stepWorkers(-1)}>-</button>
              <input type="number" value={form.workers_needed} onChange={(event) => update({ workers_needed: event.target.value })} min="1" className="stepper-input" required />
              <button type="button" className="btn ghost stepper-button" onClick={() => stepWorkers(1)}>+</button>
            </div>
          </label>
        )}
        <label>
          Notes (optional)
          <span className="st-inline">
            <input value={form.notes} onChange={(event) => update({ notes: event.target.value })} placeholder="Dress code, arrival details, requirements" />
            <button type="button" className="btn ghost compact" disabled={drafting} onClick={() => void draftPost()}>
              {drafting ? "Writing..." : "Help me write this"}
            </button>
          </span>
        </label>
        <button className="btn primary" type="submit" disabled={saving}>
          {saving ? "Saving..." : form.assigned_worker_id ? "Save draft" : "Post shift"}
        </button>
      </form>
    </div>
  );
}
