import { useState } from "react";

import type { DirectoryEntry } from "./directory";
import type { useDirectory } from "./useDirectory";
import "./TermsEditor.css";

type TermsEditorProps = {
  entry: DirectoryEntry;
  actions: ReturnType<typeof useDirectory>;
};

export function TermsEditor({ entry, actions }: TermsEditorProps) {
  const [open, setOpen] = useState(false);
  const [rate, setRate] = useState(entry.agreed_rate ?? "");
  const [hours, setHours] = useState(entry.contracted_hours_per_week ?? "");
  const saving = actions.setTerms.isPending;

  if (!open) {
    return (
      <button type="button" className="btn secondary te-toggle" onClick={() => setOpen(true)}>
        {entry.agreed_rate || entry.contracted_hours_per_week ? "Edit terms" : "Set terms"}
      </button>
    );
  }

  const save = () => {
    actions.setTerms.mutate(
      {
        workerId: entry.worker_id,
        agreed_rate: rate === "" ? null : rate,
        contracted_hours_per_week: hours === "" ? null : hours,
        default_role: entry.role || null,
      },
      { onSuccess: () => setOpen(false) }
    );
  };

  return (
    <div className="te-form">
      <label>
        Agreed rate (/hr)
        <input type="number" min="0" step="0.01" value={rate} onChange={(event) => setRate(event.target.value)} placeholder="14.50" />
      </label>
      <label>
        Contracted hours a week
        <input type="number" min="0" step="0.5" value={hours} onChange={(event) => setHours(event.target.value)} placeholder="20" />
      </label>
      <div className="te-actions">
        <button type="button" className="btn ghost compact" onClick={() => setOpen(false)}>Cancel</button>
        <button type="button" className="btn primary compact" disabled={saving} onClick={save}>
          {saving ? "Saving..." : "Save terms"}
        </button>
      </div>
    </div>
  );
}
