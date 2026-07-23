import { Icon } from "../../components/Icon";
import type { CoverageDay } from "./dashboardUtils";

type CoverageStripProps = {
  days: CoverageDay[];
};

export function CoverageStrip({ days }: CoverageStripProps) {
  return (
    <section className="card coverage-panel">
      <div className="dashboard-section-header">
        <div>
          <h2>7-Day Coverage</h2>
          <p>Open seats by day so staffing gaps are visible quickly.</p>
        </div>
      </div>
      <div className="coverage-strip">
        {days.map((day) => (
          <div key={`${day.label}-${day.date}`} className="coverage-day">
            <span>{day.label}</span>
            <strong>{day.date}</strong>
            <p>{day.totalShifts} shifts</p>
            <div className={day.openSeats > 0 ? "coverage-seat warning" : "coverage-seat"}>
              <Icon name={day.openSeats > 0 ? "alert-triangle" : "check"} size={13} />
              {day.openSeats} open seats
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
