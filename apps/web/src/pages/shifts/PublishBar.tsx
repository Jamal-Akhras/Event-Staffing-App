import { useState } from "react";

import type { RotaChange, RotaPublication } from "../../types/rota";
import { clock, shortDay } from "../dashboard/dashboardUtils";
import "./RotaPanels.css";

type PublishBarProps = {
  publications: RotaPublication[];
  people: Record<string, string>;
};

export function PublishBar({ publications, people }: PublishBarProps) {
  const [open, setOpen] = useState(false);
  if (publications.length === 0) return null;
  const latest = publications[publications.length - 1];

  return (
    <section className="rp-bar">
      <div className="rp-head">
        <span>
          <b>Published · revision {latest.revision}</b>
          <em> · {shortDay(latest.published_at)} at {clock(latest.published_at)} · {latest.assignments.length} on the rota</em>
        </span>
        <button type="button" className="btn ghost compact" onClick={() => setOpen((current) => !current)}>
          {open ? "Hide changes" : "What changed"}
        </button>
      </div>
      {open && (
        <div className="rp-history">
          {[...publications].reverse().map((publication) => (
            <div key={publication.publication_id} className="rp-revision">
              <span className="rp-revision-head">
                Revision {publication.revision}
                <em> · {shortDay(publication.published_at)} at {clock(publication.published_at)}</em>
              </span>
              <ul>
                {publication.changes.length === 0 ? (
                  <li>First publication of the week — {publication.assignments.length} assignment{publication.assignments.length === 1 ? "" : "s"}.</li>
                ) : (
                  publication.changes.map((change, index) => (
                    <li key={`${publication.publication_id}-${index}`}>{describeChange(change, people)}</li>
                  ))
                )}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function describeChange(change: RotaChange, people: Record<string, string>): string {
  const name = (id: string | null | undefined) => (id ? people[id] ?? id : "an open seat");
  if (change.kind === "added") {
    return `${name(change.worker_id)} added to ${change.role}`;
  }
  if (change.kind === "removed") {
    return `${name(change.previous_worker_id ?? change.worker_id)} removed from ${change.role}`;
  }
  if (change.kind === "reassigned") {
    return `${change.role} moved from ${name(change.previous_worker_id)} to ${name(change.worker_id)}`;
  }
  const previous =
    change.previous_start_time && change.previous_end_time
      ? `${clock(change.previous_start_time)} – ${clock(change.previous_end_time)}`
      : "its old times";
  const next =
    change.start_time && change.end_time ? `${clock(change.start_time)} – ${clock(change.end_time)}` : "new times";
  return `${change.role} (${name(change.worker_id)}) moved from ${previous} to ${next}`;
}
