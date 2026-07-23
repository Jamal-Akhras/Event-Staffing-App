import { StatusBadge } from "./StatusBadge";
import { formatMoney } from "../lib/format";
import "./ApplicationReviewCard.css";

export type Application = {
  application_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
};

export type ShiftSummary = {
  shift_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  status: string;
  workers_needed: number;
  workers_filled: number;
  currency?: string;
};

export type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  updated_at: string;
};

export type MessageHistory = {
  history_id: string;
  application_id: string;
  message: string;
  edited_at: string;
};

type ApplicationReviewCardProps = {
  application: Application;
  shift: ShiftSummary | undefined;
  worker: WorkerProfile | undefined;
  messageHistory?: MessageHistory[];
  decisionMode?: boolean;
  onApprove?: () => void;
  onReject?: () => void;
  onMessage: () => void;
  onViewProfile: () => void;
  onToggleHistory: () => void;
};

export function ApplicationReviewCard({
  application,
  shift,
  worker,
  messageHistory,
  decisionMode = false,
  onApprove,
  onReject,
  onMessage,
  onViewProfile,
  onToggleHistory,
}: ApplicationReviewCardProps) {
  const workerName = worker?.display_name ?? application.worker_id;
  const shiftTitle = shift ? `${shift.role} at ${shift.location}` : application.shift_id;
  const openSpots = shift
    ? Math.max(shift.workers_needed - shift.workers_filled, 0)
    : 0;

  return (
    <div className="application-card application-review-card">
      <div className="application-review-header">
        <div>
          <p className="booking-id" style={{ margin: 0 }}>
            Application {application.application_id.slice(0, 8)}
          </p>
          <h3 className="application-review-title">{workerName}</h3>
          <p className="booking-meta">
            {worker ? `${worker.role} - ${worker.city}` : "Worker profile unavailable"}
          </p>
        </div>
        <StatusBadge status={application.status} variant="application" />
      </div>

      <div className="application-review-grid">
        <Metric label="Reliability" value={worker ? worker.reliability_score.toFixed(1) : "n/a"} />
        <Metric label="Experience" value={worker ? `${worker.experience_years} yr` : "n/a"} />
        <Metric label="Open spots" value={shift ? `${openSpots}/${shift.workers_needed}` : "n/a"} />
      </div>

      <div className="application-review-shift">
        <p className="application-review-label">Shift</p>
        <p className="application-review-strong">{shiftTitle}</p>
        <p className="booking-meta">
          {formatDateTime(application.start_time)}
          {shift ? ` - ${formatMoney(shift.pay_rate, shift.currency)}/hr - ${shift.status}` : ""}
        </p>
      </div>

      {application.message && (
        <div className="application-review-message">
          <p className="application-review-label">Worker note</p>
          <p className="booking-meta" style={{ fontStyle: "italic" }}>
            "{application.message}"
          </p>
          <button className="btn ghost compact" type="button" onClick={onToggleHistory}>
            {messageHistory
              ? `Hide edit history (${messageHistory.length})`
              : "View edit history"}
          </button>
          {messageHistory && messageHistory.length > 0 && (
            <div className="message-history">
              {messageHistory.map((entry, index) => (
                <div key={entry.history_id} className="message-history-entry">
                  <p className="booking-meta">
                    Version {index + 1} - {formatDateTime(entry.edited_at)}
                  </p>
                  <p className="booking-meta" style={{ fontStyle: "italic" }}>
                    "{entry.message}"
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {application.decided_at && (
        <p className="booking-meta">Decided {formatDateTime(application.decided_at)}</p>
      )}

      <div className="actions">
        {decisionMode && (
          <>
            <button className="btn secondary" type="button" onClick={onApprove}>
              Approve
            </button>
            <button className="btn ghost" type="button" onClick={onReject}>
              Reject
            </button>
          </>
        )}
        <button className="btn ghost" type="button" onClick={onMessage}>
          Message
        </button>
        <button className="btn ghost" type="button" onClick={onViewProfile}>
          View profile
        </button>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="application-review-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
