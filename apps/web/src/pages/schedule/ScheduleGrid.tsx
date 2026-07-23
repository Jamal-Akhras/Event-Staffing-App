import { StatusBadge } from "../../components/StatusBadge";
import type { Shift } from "../../types/operations";
import { DAYS_OF_WEEK, formatTime } from "./scheduleUtils";

type ScheduleGridProps = {
  weekDates: Date[];
  shiftsByDay: Shift[][];
  onSelectShift: (shift: Shift) => void;
};

export function ScheduleGrid({
  weekDates,
  shiftsByDay,
  onSelectShift,
}: ScheduleGridProps) {
  return (
    <div className="schedule-grid">
      {weekDates.map((date, index) => {
        const isToday = date.toDateString() === new Date().toDateString();
        const dayShifts = shiftsByDay[index];

        return (
          <section
            key={date.toISOString()}
            className={`schedule-day ${isToday ? "today" : ""}`}
          >
            <div className="schedule-day-header">
              <span>{DAYS_OF_WEEK[index].slice(0, 3)}</span>
              <strong>{date.getDate()}</strong>
            </div>

            <div className="schedule-day-list">
              {dayShifts.length === 0 && (
                <p className="schedule-empty-day">No shifts</p>
              )}
              {dayShifts.map((shift) => (
                <button
                  key={shift.shift_id}
                  className={`schedule-shift ${shift.status}`}
                  type="button"
                  onClick={() => onSelectShift(shift)}
                >
                  <span className="schedule-shift-time">{formatTime(shift.start_time)}</span>
                  <strong>{shift.role}</strong>
                  <span>{shift.location}</span>
                  <StatusBadge status={shift.status} variant="shift" />
                </button>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
