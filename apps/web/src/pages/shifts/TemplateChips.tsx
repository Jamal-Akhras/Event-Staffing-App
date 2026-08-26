import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchJson } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import type { Template } from "../../types/templates";

type TemplateChipsProps = {
  currency: string;
  onPick: (template: Template) => void;
};

export function TemplateChips({ currency, onPick }: TemplateChipsProps) {
  const templates = useQuery({ queryKey: ["templates"], queryFn: () => fetchJson<Template[]>("/templates") });
  const list = templates.data ?? [];

  return (
    <div className="bd-again">
      <span className="bd-again-label">Post again</span>
      {list.slice(0, 4).map((template) => (
        <button key={template.template_id} type="button" className="bd-chip" onClick={() => onPick(template)}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          {template.name}
          <span>{template.workers_needed} × {formatMoney(template.pay_rate, currency)}</span>
        </button>
      ))}
      {templates.isSuccess && list.length === 0 && (
        <span className="bd-again-empty">Save a template and it appears here for one-click posting.</span>
      )}
      <Link to="/app/templates" className="bd-again-link">All templates</Link>
    </div>
  );
}
