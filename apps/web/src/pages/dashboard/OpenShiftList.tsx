import { Link } from "react-router-dom";

import { formatDateTime, formatMoney } from "../../lib/format";
import type { Shift } from "../../types/operations";

type OpenShiftListProps = {
  shifts: Shift[];
};

export function OpenShiftList({ shifts }: OpenShiftListProps) {
  return (
    <section className="card open-shifts-panel">
      <div className="dashboard-section-header">
        <div>
          <h2>Next Open Shifts</h2>
          <p>Decision-ready view of the shifts still needing coverage.</p>
        </div>
        <Link className="btn secondary" to="/app/shifts">
          View all
        </Link>
      </div>

      {shifts.length === 0 ? (
        <p className="booking-meta">No upcoming open shifts.</p>
      ) : (
        <div className="open-shift-list">
          {shifts.map((shift) => (
            <div key={shift.shift_id} className="open-shift-row">
              <div>
                <strong>{shift.role}</strong>
                <p>{shift.location}</p>
              </div>
              <div>
                <span>{formatDateTime(shift.start_time)}</span>
                <p>{formatMoney(shift.pay_rate, shift.currency)}/hr</p>
              </div>
              <div>
                <span>{shift.workers_filled} / {shift.workers_needed}</span>
                <p>filled</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
