import { Link } from "react-router-dom";

import { initials } from "../../lib/useVenue";
import type { Application, Shift, WorkerProfile } from "../../types/operations";
import { shortDay, timeRange } from "./dashboardUtils";

type DecisionListProps = {
  pending: Application[];
  shifts: Shift[];
  workers: Record<string, WorkerProfile>;
  completedCounts: Record<string, number>;
  busyId: string | null;
  onDecide: (applicationId: string, action: "approve" | "reject") => void;
};

export function DecisionList({ pending, shifts, workers, completedCounts, busyId, onDecide }: DecisionListProps) {
  const shiftsById = Object.fromEntries(shifts.map((shift) => [shift.shift_id, shift]));
  const visible = pending.slice(0, 3);

  return (
    <section className="ov-card ov-card-tight">
      <div className="ov-card-head">
        <span className="ov-kicker">Needs your decision</span>
        {pending.length > 0 && <Link to="/app/applications" className="ov-link">All {pending.length}</Link>}
      </div>
      {visible.length === 0 && <p className="ov-muted">No applications waiting. New ones land here as they arrive.</p>}
      {visible.map((application) => {
        const worker = workers[application.worker_id];
        const shift = shiftsById[application.shift_id];
        const name = worker?.display_name || "Worker";
        const worked = completedCounts[application.worker_id] ?? 0;
        const busy = busyId === application.application_id;
        return (
          <div key={application.application_id} className="ov-decision">
            <span className="ov-avatar">{initials(name)}</span>
            <div className="ov-decision-copy">
              <span className="ov-decision-name">{name}</span>
              <span className="ov-decision-meta">
                {shift?.role ?? "Shift"} · {describeWorker(worker, worked)}
              </span>
              <span className="ov-decision-when">
                {shortDay(application.start_time)} · {timeRange(application.start_time, application.end_time)}
              </span>
            </div>
            <div className="ov-decision-actions">
              <button
                type="button"
                className="ov-approve"
                disabled={busy}
                onClick={() => onDecide(application.application_id, "approve")}
              >
                Approve
              </button>
              <button
                type="button"
                className="ov-decline"
                aria-label={`Decline ${name}`}
                disabled={busy}
                onClick={() => onDecide(application.application_id, "reject")}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
          </div>
        );
      })}
    </section>
  );
}

function describeWorker(worker: WorkerProfile | undefined, worked: number) {
  const reliability = worker && worker.reliability_score > 0 ? `${Math.round(worker.reliability_score * 100)}% reliability` : "no history yet";
  const history = worked > 0 ? `worked here ${worked}×` : "new to you";
  return `${reliability} · ${history}`;
}
