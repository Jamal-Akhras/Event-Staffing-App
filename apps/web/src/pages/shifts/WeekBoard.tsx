import { formatMoney } from "../../lib/format";
import type { Application, Shift } from "../../types/operations";
import { clock } from "../dashboard/dashboardUtils";
import { appliedCount, missingSeats, sameDay, shiftsOn } from "./boardUtils";
import "./WeekBoard.css";

type WeekBoardProps = {
  days: Date[];
  shifts: Shift[];
  applications: Application[];
  now: Date;
  onAdd: (day: Date) => void;
  onSelect: (shift: Shift) => void;
};

export function WeekBoard({ days, shifts, applications, now, onAdd, onSelect }: WeekBoardProps) {
  return (
    <div className="bd-board">
      {days.map((day) => {
        const dayShifts = shiftsOn(day, shifts);
        const open = dayShifts.reduce((sum, shift) => sum + missingSeats(shift), 0);
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
            {dayShifts.map((shift) => (
              <BoardCard key={shift.shift_id} shift={shift} applied={appliedCount(shift.shift_id, applications)} onClick={() => onSelect(shift)} />
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

function BoardCard({ shift, applied, onClick }: { shift: Shift; applied: number; onClick: () => void }) {
  const missing = missingSeats(shift);
  const inactive = shift.status === "cancelled" || shift.status === "closed";
  return (
    <button type="button" className={`bd-card ${missing > 0 ? "warn" : ""} ${inactive ? "muted" : ""}`} onClick={onClick}>
      <span className="bd-card-role">{shift.role} × {shift.workers_needed}</span>
      <span className="bd-card-meta">
        {clock(shift.start_time)} – {clock(shift.end_time)} · {formatMoney(shift.pay_rate, shift.currency)}
      </span>
      {inactive ? (
        <span className="bd-card-state muted">{shift.status === "cancelled" ? "Cancelled" : "Closed"}</span>
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
