import { FormEvent, useState } from "react";

import type { Template, TemplateFormData } from "../../types/templates";
import { emptyTemplateForm } from "../../types/templates";
import "../../components/Modal.css";
import "./TemplateFormModal.css";

type TemplateFormModalProps = {
  template: Template | null;
  currencySymbol: string;
  saving: boolean;
  onClose: () => void;
  onSave: (form: TemplateFormData) => void;
};

function formFrom(template: Template | null): TemplateFormData {
  if (!template) return emptyTemplateForm;
  return {
    name: template.name,
    role: template.role,
    location: template.location,
    duration_hours: template.duration_hours,
    pay_rate: Number(template.pay_rate),
    workers_needed: template.workers_needed,
    notes: template.notes ?? "",
  };
}

export function TemplateFormModal({ template, currencySymbol, saving, onClose, onSave }: TemplateFormModalProps) {
  const [form, setForm] = useState<TemplateFormData>(() => formFrom(template));
  const update = (patch: Partial<TemplateFormData>) => setForm((current) => ({ ...current, ...patch }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSave(form);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="card modal tp-modal" onClick={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <div>
            <h2>{template ? "Edit template" : "New template"}</h2>
            <p className="tp-modal-hint">Saved details are pre-filled every time you post this shift.</p>
          </div>
          <button type="button" className="btn ghost" onClick={onClose}>
            Close
          </button>
        </header>

        <form className="form modal-body" onSubmit={submit}>
          <label>
            Name
            <input
              value={form.name}
              onChange={(event) => update({ name: event.target.value })}
              placeholder="Saturday bar team"
              required
            />
          </label>
          <div className="tp-form-pair">
            <label>
              Role
              <input
                value={form.role}
                onChange={(event) => update({ role: event.target.value })}
                placeholder="Bartender"
                required
              />
            </label>
            <label>
              Location
              <input
                value={form.location}
                onChange={(event) => update({ location: event.target.value })}
                placeholder="Main bar"
                required
              />
            </label>
          </div>
          <div className="tp-form-trio">
            <label>
              People
              <input
                type="number"
                min="1"
                value={form.workers_needed}
                onChange={(event) => update({ workers_needed: Number(event.target.value) })}
                required
              />
            </label>
            <label>
              Hours
              <input
                type="number"
                min="0.5"
                max="24"
                step="0.5"
                value={form.duration_hours}
                onChange={(event) => update({ duration_hours: Number(event.target.value) })}
                required
              />
            </label>
            <label>
              Pay ({currencySymbol}/hr)
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.pay_rate}
                onChange={(event) => update({ pay_rate: Number(event.target.value) })}
                required
              />
            </label>
          </div>
          <label>
            Notes
            <textarea
              rows={3}
              value={form.notes}
              onChange={(event) => update({ notes: event.target.value })}
              placeholder="Dress code, which door to use, who to ask for"
            />
          </label>
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Saving…" : template ? "Save changes" : "Save template"}
          </button>
        </form>
      </section>
    </div>
  );
}
