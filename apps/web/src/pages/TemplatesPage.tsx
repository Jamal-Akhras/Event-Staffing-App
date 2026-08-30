import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { PageHeader } from "../components/PageHeader";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { fetchJson } from "../lib/api";
import { daysInMonth, startOfMonth, useVenueOverview } from "../lib/useInsights";
import { currencySymbol, formatMoney } from "../lib/format";
import { initials, useVenue } from "../lib/useVenue";
import type { Template } from "../types/templates";
import { StatRow } from "./dashboard/StatRow";
import { GenerateRun } from "./templates/GenerateRun";
import { TemplateFormModal } from "./templates/TemplateFormModal";
import { useTemplateActions, useTemplates } from "./templates/useTemplates";
import "./TemplatesPage.css";

export function TemplatesPage() {
  const { toast } = useToast();
  const venue = useVenue();
  const templates = useTemplates();
  const now = new Date();
  const month = useVenueOverview(startOfMonth(now), daysInMonth(now));
  const actions = useTemplateActions((type, message) => toast({ type, message }));
  const [editing, setEditing] = useState<Template | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [runTemplateId, setRunTemplateId] = useState("");
  const runRef = useRef<HTMLDivElement>(null);

  if (templates.error) return <ErrorCard message={(templates.error as Error).message} />;
  if (templates.isPending) {
    return (
      <div className="pg">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={6} />
      </div>
    );
  }

  const list = templates.data;
  const currency = venue.data?.currency ?? "GBP";
  const scheduled = (month.data?.days ?? []).reduce((sum, day) => sum + day.total_shifts, 0);
  const openSeats = month.data?.open_seats ?? 0;

  const openForm = (template: Template | null) => {
    setEditing(template);
    setFormOpen(true);
  };

  const useInRun = (template: Template) => {
    setRunTemplateId(template.template_id);
    runRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="pg">
      <PageHeader
        title="Templates"
        lead="The shifts you run every week, saved once."
        emphasis={list.length > 0 ? "Post a month of them in one go." : undefined}
        actions={
          <button type="button" className="btn primary" onClick={() => openForm(null)}>
            New template
          </button>
        }
      />

      <StatRow
        stats={[
          {
            label: "Templates saved",
            value: String(list.length),
            note: list.length === 0 ? "Save your first one to post faster" : "Ready to post or generate",
          },
          {
            label: "Shifts this month",
            value: String(scheduled),
            note: "Everything on the board in the current month",
          },
          {
            label: "Open seats",
            value: String(openSeats),
            note: openSeats > 0 ? "Still to fill across open shifts" : "Everything posted is covered",
            tone: openSeats > 0 ? "warning" : "success",
          },
        ]}
      />

      {list.length > 0 && (
        <div ref={runRef}>
          <GenerateRun
            templates={list}
            templateId={runTemplateId || list[0].template_id}
            currency={currency}
            busy={actions.generate.isPending}
            onTemplateChange={setRunTemplateId}
            onGenerate={(request) => actions.generate.mutate(request)}
          />
        </div>
      )}

      {list.length === 0 ? (
        <EmptyState
          title="No templates yet"
          message="Save the shifts you run again and again, then post a whole month of them from here."
          action={{ label: "New template", onClick: () => openForm(null) }}
        />
      ) : (
        <div className="tp-grid">
          {list.map((template) => {
            const perShift = template.workers_needed * template.duration_hours * Number(template.pay_rate);
            return (
              <article key={template.template_id} className="tp-card">
                <div className="tp-card-top">
                  <span className="tp-mark">{initials(template.name)}</span>
                  <div>
                    <h3>{template.name}</h3>
                    <p>
                      {template.role} · {template.location}
                    </p>
                  </div>
                </div>

                <div className="tp-facts">
                  <div>
                    <span>People</span>
                    <b>{template.workers_needed}</b>
                  </div>
                  <div>
                    <span>Hours</span>
                    <b>{template.duration_hours}</b>
                  </div>
                  <div>
                    <span>Pay</span>
                    <b>{formatMoney(template.pay_rate, currency)}</b>
                  </div>
                </div>

                {template.notes && <p className="tp-note">{template.notes}</p>}

                <div className="tp-card-foot">
                  <span className="tp-cost">
                    {formatMoney(perShift, currency)} <em>per shift</em>
                  </span>
                  <span className="tp-card-acts">
                    <button type="button" className="btn primary compact" onClick={() => useInRun(template)}>
                      Use in a run
                    </button>
                    <button type="button" className="btn ghost compact" onClick={() => openForm(template)}>
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn ghost compact tp-delete"
                      aria-label={`Delete ${template.name}`}
                      disabled={actions.remove.isPending}
                      onClick={() => {
                        if (window.confirm(`Delete the ${template.name} template? Shifts already posted are unaffected.`)) {
                          actions.remove.mutate(template.template_id);
                        }
                      }}
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" aria-hidden="true">
                        <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v6M14 11v6" />
                      </svg>
                    </button>
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {formOpen && (
        <TemplateFormModal
          template={editing}
          currencySymbol={currencySymbol(currency)}
          saving={actions.save.isPending}
          onClose={() => setFormOpen(false)}
          onSave={(form) =>
            actions.save.mutate(
              { template: editing, form },
              { onSuccess: () => setFormOpen(false) }
            )
          }
        />
      )}
    </div>
  );
}
