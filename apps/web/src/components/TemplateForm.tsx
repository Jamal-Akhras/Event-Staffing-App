import { FormEvent } from "react";
import { Template, TemplateFormData } from "../types/templates";

type TemplateFormProps = {
  editingTemplate: Template | null;
  formData: TemplateFormData;
  onChange: (formData: TemplateFormData) => void;
  onSubmit: (event: FormEvent) => void;
  onCancel: () => void;
};

export function TemplateForm({
  editingTemplate,
  formData,
  onChange,
  onSubmit,
  onCancel,
}: TemplateFormProps) {
  return (
    <div className="card" style={{ padding: "24px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "1.3rem" }}>
          {editingTemplate ? "Edit Template" : "New Template"}
        </h2>
        <button className="btn ghost" type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>

      <form onSubmit={onSubmit} className="form">
        <label>
          <span style={{ fontWeight: 600 }}>Template Name</span>
          <input
            type="text"
            value={formData.name}
            onChange={(event) => onChange({ ...formData, name: event.target.value })}
            placeholder="e.g., Saturday Night Bar Shift"
            required
          />
        </label>

        <div className="template-form-grid two">
          <label>
            <span style={{ fontWeight: 600 }}>Role</span>
            <input
              type="text"
              value={formData.role}
              onChange={(event) => onChange({ ...formData, role: event.target.value })}
              placeholder="e.g., Bartender"
              required
            />
          </label>
          <label>
            <span style={{ fontWeight: 600 }}>Location</span>
            <input
              type="text"
              value={formData.location}
              onChange={(event) => onChange({ ...formData, location: event.target.value })}
              placeholder="e.g., Downtown"
              required
            />
          </label>
        </div>

        <div className="template-form-grid three">
          <NumberField label="Duration (hours)" value={formData.duration_hours}
            onChange={(value) => onChange({ ...formData, duration_hours: value })} step="0.5" />
          <NumberField label="Pay Rate ($/hr)" value={formData.pay_rate}
            onChange={(value) => onChange({ ...formData, pay_rate: value })} step="0.01" />
          <NumberField label="Workers Needed" value={formData.workers_needed}
            onChange={(value) => onChange({ ...formData, workers_needed: value })} min="1" />
        </div>

        <label>
          <span style={{ fontWeight: 600 }}>Notes (optional)</span>
          <textarea
            value={formData.notes}
            onChange={(event) => onChange({ ...formData, notes: event.target.value })}
            placeholder="Any additional details..."
            rows={3}
            className="template-notes"
          />
        </label>

        <button type="submit" className="btn primary">
          {editingTemplate ? "Update Template" : "Create Template"}
        </button>
      </form>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  step,
  min,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: string;
  min?: string;
}) {
  return (
    <label>
      <span style={{ fontWeight: 600 }}>{label}</span>
      <input
        type="number"
        step={step}
        min={min}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        required
      />
    </label>
  );
}
