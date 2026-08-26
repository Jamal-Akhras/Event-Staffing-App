import { Link } from "react-router-dom";

import type { CoverageDay } from "./dashboardUtils";

export function WeekStrip({ days }: { days: CoverageDay[] }) {
  const firstGap = days.findIndex((day) => day.openSeats > 0);
  return (
    <section className="ov-card ov-card-tight">
      <div className="ov-card-head">
        <span className="ov-kicker">This week</span>
        <Link to="/app/shifts" className="ov-link">Open the board</Link>
      </div>
      <div className="ov-week">
        {days.map((day, index) => (
          <div key={day.label + day.dayNumber} className={`ov-day ${index === firstGap ? "gap" : ""}`}>
            <span className={`ov-day-label ${day.openSeats > 0 ? "warn" : ""}`}>{day.label}</span>
            <span className="ov-day-number">{day.dayNumber}</span>
            {day.totalShifts === 0 ? (
              <span className="ov-day-state muted">No shifts</span>
            ) : day.openSeats > 0 ? (
              <span className="ov-day-state warn">{day.openSeats} open</span>
            ) : (
              <span className="ov-day-state ok">Covered</span>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
