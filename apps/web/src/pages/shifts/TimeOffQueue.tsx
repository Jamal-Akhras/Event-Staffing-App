import type { TimeOffRequest } from "../../types/workforce";
import "./TimeOffQueue.css";

type TimeOffQueueProps = {
  requests: TimeOffRequest[];
  people: Record<string, string>;
  timezone: string;
  loading: boolean;
  error: Error | null;
  busyId: string | null;
  onDecide: (requestId: string, action: "approve" | "decline") => void;
};

export function TimeOffQueue({
  requests,
  people,
  timezone,
  loading,
  error,
  busyId,
  onDecide,
}: TimeOffQueueProps) {
  return (
    <section className="ov-card ov-card-tight toq-card">
      <div className="ov-card-head">
        <span className="ov-kicker">Time off</span>
        {requests.length > 0 && <span className="toq-count">{requests.length} waiting</span>}
      </div>
      {loading && <p className="ov-muted">Loading requests…</p>}
      {error && <p className="toq-error">Requests could not be loaded. Try again shortly.</p>}
      {!loading && !error && requests.length === 0 && (
        <p className="ov-muted">Everyone’s requests are up to date.</p>
      )}
      {requests.slice(0, 4).map((request) => {
        const name = people[request.worker_id] || "Team member";
        const busy = busyId === request.request_id;
        return (
          <article className="toq-request" key={request.request_id}>
            <div className="toq-copy">
              <strong>{name}</strong>
              <span>{dateRange(request.start_time, request.end_time, timezone)}</span>
              <p>{request.reason}</p>
            </div>
            <div className="toq-actions">
              <button
                type="button"
                className="ov-approve"
                disabled={busy}
                onClick={() => onDecide(request.request_id, "approve")}
              >
                Approve
              </button>
              <button
                type="button"
                className="toq-decline"
                disabled={busy}
                onClick={() => onDecide(request.request_id, "decline")}
              >
                Decline
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}

function dateRange(start: string, end: string, timezone: string): string {
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    day: "numeric",
    month: "short",
  });
  return `${formatter.format(new Date(start))} – ${formatter.format(new Date(end))}`;
}
