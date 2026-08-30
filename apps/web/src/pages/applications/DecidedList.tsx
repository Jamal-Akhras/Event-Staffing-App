import { EmptyState } from "../../components/EmptyState";
import { initials } from "../../lib/useVenue";
import type { Application, Booking, Shift, WorkerProfile } from "../../types/operations";
import { clock, shortDay } from "../dashboard/dashboardUtils";
import { statusLabel } from "./applicationsUtils";

const CANCELLABLE = new Set(["confirmed", "checked_in"]);

type DecidedListProps = {
  applications: Application[];
  shifts: Shift[];
  workers: Record<string, WorkerProfile>;
  bookings: Record<string, Booking>;
  emptyTitle: string;
  emptyMessage: string;
  onMessage: (application: Application) => void;
  onCancel?: (application: Application) => void;
};

export function DecidedList({
  applications,
  shifts,
  workers,
  bookings,
  emptyTitle,
  emptyMessage,
  onMessage,
  onCancel,
}: DecidedListProps) {
  const shiftsById = Object.fromEntries(shifts.map((shift) => [shift.shift_id, shift]));

  if (applications.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <section className="ap-group">
      {applications.map((application) => {
        const shift = shiftsById[application.shift_id];
        const worker = workers[application.worker_id];
        const booking = application.booking_id ? bookings[application.booking_id] : undefined;
        const name = worker?.display_name || "Worker";
        const label = statusLabel(application, booking);
        const cancellable = Boolean(onCancel && booking && CANCELLABLE.has(booking.state));
        return (
          <div key={application.application_id} className="ap-row">
            <span className="ap-avatar">{initials(name)}</span>
            <div className="ap-who">
              <b>{name}</b>
              <span className="ap-evidence">
                {shift ? `${shift.role} · ${shortDay(shift.start_time)} · ${clock(shift.start_time)} – ${clock(shift.end_time)}` : "Shift removed"}
              </span>
            </div>
            <div className="ap-acts">
              <span className={`ap-status ${label.startsWith("Cancelled") || label === "No-show" ? "bad" : ""}`}>{label}</span>
              <button type="button" className="btn ghost compact" onClick={() => onMessage(application)}>
                Message
              </button>
              {cancellable && onCancel && (
                <button type="button" className="btn ghost compact ap-danger" onClick={() => onCancel(application)}>
                  Cancel booking
                </button>
              )}
            </div>
          </div>
        );
      })}
    </section>
  );
}
