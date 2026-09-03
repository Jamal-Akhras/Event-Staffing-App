import { formatMoney } from "../../lib/format";
import { calendarDayLabel, venueClock } from "../../lib/venueTime";
import { RELATIONSHIP_LABELS, type RelationshipType } from "../../types/workforce";
import type { TimesheetDay, TimesheetWeek, TimesheetWorker } from "../../types/rota";

const SOURCE_LABELS: Record<TimesheetDay["hours_source"], string> = {
  clocked: "Clocked",
  adjusted: "Adjusted",
  venue_recorded: "Recorded",
  scheduled: "Scheduled",
  approved: "Approved",
};

type TimesheetTableProps = {
  week: TimesheetWeek;
  currency: string;
  timezone: string;
  selected: Set<string>;
  onToggle: (bookingId: string) => void;
  onAdjust: (day: TimesheetDay) => void;
  onRecord: (day: TimesheetDay) => void;
  onCorrect: (day: TimesheetDay) => void;
};

export function TimesheetTable({ week, currency, timezone, selected, onToggle, onAdjust, onRecord, onCorrect }: TimesheetTableProps) {
  if (week.workers.length === 0) {
    return <p className="ts-empty">No shifts fall in this week yet.</p>;
  }

  return (
    <div className="ts-scroll">
      <table className="ts-table">
        <thead>
          <tr>
            <th className="ts-check" aria-label="Select" />
            <th>Day</th>
            <th>Role</th>
            <th>Scheduled</th>
            <th>Worked</th>
            <th>Approved</th>
            <th className="ts-actions-col" aria-label="Actions" />
          </tr>
        </thead>
        {week.workers.map((worker) => (
          <tbody key={worker.worker_id}>
            <tr className="ts-worker">
              <td colSpan={5}>
                <b>{worker.display_name}</b>
                <em>
                  {" "}· {RELATIONSHIP_LABELS[worker.relationship_type as RelationshipType] ?? worker.relationship_type}
                  {worker.contracted_hours_per_week ? ` · contracted ${worker.contracted_hours_per_week}h/week` : ""}
                </em>
              </td>
              <td colSpan={2} className="ts-worker-totals">
                {worker.scheduled_hours}h planned · {worker.worked_hours}h worked · {worker.approved_hours}h approved
              </td>
            </tr>
            {worker.days.map((day) => (
              <DayRow
                key={day.booking_id}
                day={day}
                worker={worker}
                currency={currency}
                timezone={timezone}
                selected={selected.has(day.booking_id)}
                onToggle={() => onToggle(day.booking_id)}
                onAdjust={() => onAdjust(day)}
                onRecord={() => onRecord(day)}
                onCorrect={() => onCorrect(day)}
              />
            ))}
          </tbody>
        ))}
        <tfoot>
          <tr>
            <td />
            <td colSpan={2}>Week total</td>
            <td>{week.total_scheduled_hours}h</td>
            <td>{week.total_worked_hours}h</td>
            <td>
              {week.total_approved_hours}h · {formatMoney(week.total_approved_wages, currency)}
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function DayRow({
  day,
  worker,
  currency,
  timezone,
  selected,
  onToggle,
  onAdjust,
  onRecord,
  onCorrect,
}: {
  day: TimesheetDay;
  worker: TimesheetWorker;
  currency: string;
  timezone: string;
  selected: boolean;
  onToggle: () => void;
  onAdjust: () => void;
  onRecord: () => void;
  onCorrect: () => void;
}) {
  const approvable = day.state === "checked_out" && day.approved_hours === null;
  const adjustable = approvable;
  const recordable = day.state === "confirmed" && day.attendance_mode === "employed";
  const correctable = day.approved_hours !== null && day.charge_id !== null;
  const workerLabel = worker.display_name;

  return (
    <>
      <tr className={day.state === "no_show" ? "ts-muted" : ""}>
      <td className="ts-check">
        {approvable && (
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggle}
            aria-label={`Select ${workerLabel} on ${calendarDayLabel(day.day)}`}
          />
        )}
      </td>
      <td>{calendarDayLabel(day.day)}</td>
      <td>
        {day.role}
        {day.attendance_mode === "employed" && <span className="ts-tag">Staff</span>}
      </td>
      <td>
        {venueClock(day.scheduled_start, timezone)} – {venueClock(day.scheduled_end, timezone)} · {day.scheduled_hours}h
      </td>
      <td>
        {day.worked_hours !== null ? `${day.worked_hours}h` : "—"}
        <span className={`ts-source ${day.hours_source}`}>{SOURCE_LABELS[day.hours_source]}</span>
      </td>
      <td>
        {day.approved_hours !== null ? (
          <>
            {day.approved_hours}h
            {day.approved_wages !== null ? ` · ${formatMoney(day.approved_wages, currency)}` : ""}
            {Number(day.adjustments_total_hours) !== 0 && (
              <span className="ts-tag warn">{Number(day.adjustments_total_hours) > 0 ? "+" : ""}{day.adjustments_total_hours}h corrected</span>
            )}
          </>
        ) : (
          "—"
        )}
      </td>
      <td className="ts-actions-col">
        <span className="ts-actions">
          {recordable && (
            <button type="button" className="btn ghost compact" onClick={onRecord}>Record attendance</button>
          )}
          {adjustable && (
            <button type="button" className="btn ghost compact" onClick={onAdjust}>Adjust hours</button>
          )}
          {correctable && (
            <button type="button" className="btn ghost compact" onClick={onCorrect}>Correct hours</button>
          )}
        </span>
      </td>
      </tr>
      {day.adjustments.map((adjustment) => (
        <tr className="ts-correction" key={adjustment.adjustment_id}>
          <td />
          <td>Correction</td>
          <td colSpan={2}>{adjustment.reason}</td>
          <td>{Number(adjustment.delta_hours) > 0 ? "+" : ""}{adjustment.delta_hours}h</td>
          <td>
            {formatMoney(adjustment.delta_wages, currency)} wages
            {Number(adjustment.delta_fee) !== 0 && ` · ${formatMoney(adjustment.delta_fee, currency)} fee`}
          </td>
          <td />
        </tr>
      ))}
    </>
  );
}
