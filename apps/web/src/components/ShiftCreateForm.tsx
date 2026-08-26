import { FormEvent, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { postJson } from "../lib/api";
import "./ShiftCreateForm.css";

const CURRENCY_SYMBOL: Record<string, string> = {
  GBP: "£",
  AED: "د.إ",
  USD: "$",
  EUR: "€",
};

type ShiftCreateFormProps = {
  onCreated: () => Promise<void>;
  onError: (message: string) => void;
};

export function ShiftCreateForm({ onCreated, onError }: ShiftCreateFormProps) {
  const { user } = useAuth();
  const currency = user?.currency ?? "GBP";
  const symbol = CURRENCY_SYMBOL[currency] ?? currency;
  const [shiftForm, setShiftForm] = useState({
    role: "Server",
    location: "Downtown",
    start_time: "",
    end_time: "",
    pay_rate: "25",
    workers_needed: "1",
    notes: "",
  });

  const handleCreateShift = async (event: FormEvent) => {
    event.preventDefault();

    try {
      await postJson("/shifts", {
        role: shiftForm.role,
        location: shiftForm.location,
        start_time: new Date(shiftForm.start_time).toISOString(),
        end_time: new Date(shiftForm.end_time).toISOString(),
        pay_rate: Number(shiftForm.pay_rate),
        workers_needed: Number(shiftForm.workers_needed),
        notes: shiftForm.notes || null,
        now: new Date().toISOString(),
      });
      await onCreated();
      setShiftForm({ ...shiftForm, start_time: "", end_time: "", notes: "" });
    } catch (err) {
      onError((err as Error).message);
    }
  };

  return (
    <div className="panel card">
      <div className="panel-title">
        <h3>Create Shift</h3>
        <span className="pill">Venue</span>
      </div>
      <form className="form" onSubmit={handleCreateShift}>
        <label>
          Role
          <input
            value={shiftForm.role}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, role: event.target.value })
            }
            placeholder="e.g., Server, Bartender, Host"
            required
          />
        </label>
        <label>
          Location
          <input
            value={shiftForm.location}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, location: event.target.value })
            }
            placeholder="e.g., Main room, terrace, banquet hall"
            required
          />
        </label>
        <label>
          Start time
          <input
            type="datetime-local"
            value={shiftForm.start_time}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, start_time: event.target.value })
            }
            required
          />
        </label>
        <label>
          End time
          <input
            type="datetime-local"
            value={shiftForm.end_time}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, end_time: event.target.value })
            }
            required
          />
        </label>
        <label>
          Pay rate ({symbol}/hr)
          <input
            type="number"
            value={shiftForm.pay_rate}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, pay_rate: event.target.value })
            }
            min="0"
            step="0.01"
            required
          />
        </label>
        <label>
          Workers needed
          <div className="stepper-control">
            <button
              type="button"
              className="btn ghost stepper-button"
              onClick={() => updateWorkersNeeded(-1)}
            >
              -
            </button>
            <input
              type="number"
              value={shiftForm.workers_needed}
              onChange={(event) =>
                setShiftForm({ ...shiftForm, workers_needed: event.target.value })
              }
              min="1"
              className="stepper-input"
              required
            />
            <button
              type="button"
              className="btn ghost stepper-button"
              onClick={() => updateWorkersNeeded(1)}
            >
              +
            </button>
          </div>
        </label>
        <label>
          Notes (optional)
          <input
            value={shiftForm.notes}
            onChange={(event) =>
              setShiftForm({ ...shiftForm, notes: event.target.value })
            }
            placeholder="Dress code, arrival details, requirements"
          />
        </label>
        <button className="btn primary" type="submit">
          Post shift
        </button>
      </form>
    </div>
  );

  function updateWorkersNeeded(delta: number) {
    const current = Number(shiftForm.workers_needed) || 1;
    setShiftForm({
      ...shiftForm,
      workers_needed: String(Math.max(current + delta, 1)),
    });
  }
}
