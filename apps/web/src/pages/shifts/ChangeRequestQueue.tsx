import type { ShiftChangeRequest } from "../../types/workforce";
import "./TimeOffQueue.css";

type ChangeRequestQueueProps = {
  requests: ShiftChangeRequest[];
  people: Record<string, string>;
  timezone: string;
  loading: boolean;
  error: Error | null;
  busyId: string | null;
  onDecide: (requestId: string, action: "approve" | "decline") => void;
};

export function ChangeRequestQueue({
  requests,
  people,
  timezone,
  loading,
  error,
  busyId,
  onDecide,
}: ChangeRequestQueueProps) {
  return (
    <section className="ov-card ov-card-tight toq-card">
      <div className="ov-card-head">
        <span className="ov-kicker">Shift changes</span>
        {requests.length > 0 && <span className="toq-count">{requests.length} waiting</span>}
      </div>
      {loading && <p className="ov-muted">Loading requests…</p>}
      {error && <p className="toq-error">Requests could not be loaded. Try again shortly.</p>}
      {!loading && !error && requests.length === 0 && (
        <p className="ov-muted">No one is asking to change a shift.</p>
      )}
      {requests.slice(0, 4).map((request) => {
        const name = people[request.worker_id] || "Team member";
        const busy = busyId === request.request_id;
        return (
          <article className="toq-request" key={request.request_id}>
            <div className="toq-copy">
              <strong>{headline(request, name, people)}</strong>
              <span>{shiftLine(request, timezone)}</span>
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

function headline(
  request: ShiftChangeRequest,
  name: string,
  people: Record<string, string>,
): string {
  if (request.change_type === "release") return `${name} asks to be released`;
  const replacement =
    (request.replacement_worker_id && people[request.replacement_worker_id]) || "a colleague";
  return `${name} hands over to ${replacement}`;
}

function shiftLine(request: ShiftChangeRequest, timezone: string): string {
  if (!request.shift) return "Shift details unavailable";
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${request.shift.role} · ${formatter.format(new Date(request.shift.start_time))}`;
}
