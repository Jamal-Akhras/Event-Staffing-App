import { useAuth } from "../contexts/AuthContext";
import { formatMoney } from "../lib/format";
import { Template } from "../types/templates";

type TemplateCardProps = {
  template: Template;
  onEdit: () => void;
  onDelete: () => void;
};

export function TemplateCard({ template, onEdit, onDelete }: TemplateCardProps) {
  const { user } = useAuth();
  const currency = user?.currency ?? "GBP";
  return (
    <div className="card template-card">
      <div className="template-card-header">
        <div>
          <h3>{template.name}</h3>
          <p>{template.role} - {template.location}</p>
        </div>
      </div>

      <div className="template-card-meta">
        <p className="booking-meta">
          {template.duration_hours} {template.duration_hours === 1 ? "hour" : "hours"}
        </p>
        <p className="booking-meta">{formatMoney(template.pay_rate, currency)}/hr</p>
        <p className="booking-meta">
          {template.workers_needed} {template.workers_needed === 1 ? "worker" : "workers"} needed
        </p>
      </div>

      {template.notes && (
        <p className="template-card-note">
          "{template.notes}"
        </p>
      )}

      <div className="template-card-actions">
        <button className="btn secondary" onClick={onEdit}>
          Edit
        </button>
        <button className="btn ghost" type="button" onClick={onDelete}>
          Delete
        </button>
      </div>
    </div>
  );
}
