import { formatMoney } from "../../lib/format";
import { initials } from "../../lib/useVenue";
import { clock, shortDay } from "../dashboard/dashboardUtils";
import { evidenceFor, type Applicant, type ShiftGroup as Group } from "./applicationsUtils";

type ShiftGroupProps = {
  group: Group;
  now: Date;
  selectedId: string | null;
  busyId: string | null;
  onSelect: (applicant: Applicant) => void;
  onDecide: (applicationId: string, action: "approve" | "reject") => void;
};

export function ShiftGroup({ group, now, selectedId, busyId, onSelect, onDecide }: ShiftGroupProps) {
  const { shift, openSeats, urgent, applicants } = group;
  const filled = shift.workers_needed - openSeats;

  return (
    <section className={`ap-group ${urgent ? "urgent" : ""}`}>
      <header className="ap-group-head">
        <span className="ap-role">{shift.role} × {shift.workers_needed}</span>
        <span className="ap-when">
          {shortDay(shift.start_time)} · {clock(shift.start_time)} – {clock(shift.end_time)} ·{" "}
          {formatMoney(shift.pay_rate, shift.currency)}/hr · {shift.location}
        </span>
        <span className={`ap-seats ${openSeats === 0 ? "ok" : ""}`}>
          <span className="ap-meter" aria-hidden="true">
            {Array.from({ length: shift.workers_needed }, (_, index) => (
              <i key={index} className={index < filled ? "f" : ""} />
            ))}
          </span>
          {openSeats === 0 ? "All seats filled" : `${filled} of ${shift.workers_needed} filled`}
        </span>
      </header>

      {applicants.map((applicant) => {
        const { application, worker, workedHere } = applicant;
        const evidence = evidenceFor(applicant, now);
        const name = worker?.display_name || "Worker";
        const busy = busyId === application.application_id;
        const full = openSeats === 0;
        return (
          <div
            key={application.application_id}
            className={`ap-row ${selectedId === application.application_id ? "sel" : ""} ${full ? "dim" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(applicant)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect(applicant);
              }
            }}
          >
            <span className="ap-avatar">{initials(name)}</span>
            <div className="ap-who">
              <b>
                {name}
                {workedHere >= 3 && <span className="ap-pill reg">Regular</span>}
                {workedHere === 0 && <span className="ap-pill new">New to you</span>}
              </b>
              <span className="ap-evidence">
                <em className={evidence.tone}>{evidence.reliability}</em> · {evidence.history} · {evidence.applied}
              </span>
              {application.message && <span className="ap-note">“{application.message}”</span>}
            </div>
            <div className="ap-acts">
              <button
                type="button"
                className="btn primary compact"
                disabled={busy || full}
                onClick={(event) => {
                  event.stopPropagation();
                  onDecide(application.application_id, "approve");
                }}
              >
                {full ? "No seats left" : "Approve"}
              </button>
              <button
                type="button"
                className="btn ghost compact ap-decline"
                aria-label={`Decline ${name}`}
                disabled={busy}
                onClick={(event) => {
                  event.stopPropagation();
                  onDecide(application.application_id, "reject");
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
          </div>
        );
      })}

      {openSeats === 0 && (
        <p className="ap-foot">Declining tells people quickly, so they can pick up work elsewhere.</p>
      )}
    </section>
  );
}
