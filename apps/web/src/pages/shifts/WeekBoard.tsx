import { formatMoney } from "../../lib/format";
import { initials } from "../../lib/useVenue";
import { venueClock } from "../../lib/venueTime";
import type { Application, Shift } from "../../types/operations";
import { appliedCount, missingSeats, projectedCost, sameDay, seatsOn, shiftsOn } from "./boardUtils";
import "./WeekBoard.css";

type WeekBoardProps = {
  days: Date[];
  shifts: Shift[];
  applications: Application[];
  people: Record<string, string>;
  currency: string;
  now: Date;
  timezone: string;
  onAdd: (day: Date) => void;
  onSelect: (shift: Shift) => void;
};

export function WeekBoard({ days, shifts, applications, people, currency, now, timezone, onAdd, onSelect }: WeekBoardProps) {
  return (
    <div className="bd-board">
      {days.map((day) => {
        const dayShifts = shiftsOn(day, shifts, timezone);
        const open = dayShifts.reduce((sum, shift) => sum + missingSeats(shift), 0);
        const cost = projectedCost(dayShifts);
        const seats = seatsOn(dayShifts);
        const today = sameDay(day, now);
        const weekday = day.toLocaleDateString("en-GB", { weekday: "short" });
        return (
          <div key={day.toISOString()} className={`bd-col ${open > 0 ? "warn" : ""} ${today ? "today" : ""}`}>
            <div className="bd-col-head">
              <span className={`bd-col-label ${today ? "today" : open > 0 ? "warn" : ""}`}>
                {weekday}{today ? " · today" : ""}{open > 0 ? ` · ${open} open` : ""}
              </span>
              <span className="bd-col-number">{day.getDate()}</span>
            </div>
            {seats > 0 && (
              <span className="bd-col-cost">
                {formatMoney(cost, currency)} · {seats} on
              </span>
            )}
            {dayShifts.map((shift) => (
              <BoardCard
                key={shift.shift_id}
                shift={shift}
                applied={appliedCount(shift.shift_id, applications)}
                person={shift.assigned_worker_id ? people[shift.assigned_worker_id] ?? null : null}
                timezone={timezone}
                onClick={() => onSelect(shift)}
              />
            ))}
            <button type="button" className="bd-add" onClick={() => onAdd(day)}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Add
            </button>
          </div>
        );
      })}
    </div>
  );
}

function tintFor(shift: Shift) {
  if (shift.origin === "assigned") return "tint-team";
  if (shift.origin === "pool") return "tint-pool";
  if (shift.origin === "market") return "tint-market";
  return "";
}

function BoardCard({
  shift,
  applied,
  person,
  timezone,
  onClick,
}: {
  shift: Shift;
  applied: number;
  person: string | null;
  timezone: string;
  onClick: () => void;
}) {
  const missing = missingSeats(shift);
  const inactive = shift.status === "cancelled" || shift.status === "closed";
  const draft = shift.rota_state === "draft";
  const attention = shift.needs_attention === true;
  return (
    <button
      type="button"
      className={`bd-card ${tintFor(shift)} ${missing > 0 ? "warn open" : ""} ${inactive ? "muted" : ""}`}
      onClick={onClick}
    >
      <span className="bd-card-role">{shift.role}{shift.workers_needed > 1 ? ` × ${shift.workers_needed}` : ""}</span>
      <span className="bd-card-meta">
        {venueClock(shift.start_time, timezone)} – {venueClock(shift.end_time, timezone)} · {formatMoney(shift.pay_rate, shift.currency)}
      </span>
      {person && (
        <span className="bd-chip">
          <span className="bd-chip-mark">{initials(person)}</span>
          {person}
        </span>
      )}
      {(draft || attention) && (
        <span className="bd-flags">
          {shift.required_certification && (
            <span className="bd-badge">Requires {shift.required_certification}</span>
          )}
          {draft && <span className="bd-badge">Draft</span>}
          {attention && <span className="bd-badge warn">Needs attention</span>}
        </span>
      )}
      {inactive ? (
        <span className="bd-card-state muted">{shift.status === "cancelled" ? "Cancelled" : "Closed"}</span>
      ) : draft ? (
        <span className="bd-card-state muted">Not published yet</span>
      ) : missing > 0 ? (
        <span className="bd-card-state warn">
          {shift.workers_filled} of {shift.workers_needed} · {applied} applied
        </span>
      ) : (
        <span className="bd-card-state ok">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 13l4 4L19 7" />
          </svg>
          Filled
        </span>
      )}
    </button>
  );
}
