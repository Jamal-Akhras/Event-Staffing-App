import { StatusBadge } from "../../components/StatusBadge";
import { formatMoney } from "../../lib/format";
import type { Shift } from "../../types/operations";
import { formatDateTime, formatLongDate, formatTime } from "./scheduleUtils";

type ShiftDetailsModalProps = {
  shift: Shift;
  onClose: () => void;
};

export function ShiftDetailsModal({ shift, onClose }: ShiftDetailsModalProps) {
  return (
    <div className="schedule-modal-backdrop" onClick={onClose}>
      <section className="card schedule-modal" onClick={(event) => event.stopPropagation()}>
        <div className="schedule-modal-header">
          <div>
            <h2>{shift.role}</h2>
            <p className="booking-id">{shift.shift_id}</p>
          </div>
          <button className="btn ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="schedule-modal-body">
          <Detail label="Date" value={formatLongDate(shift.start_time)} />
          <Detail
            label="Time"
            value={`${formatTime(shift.start_time)} - ${formatTime(shift.end_time)}`}
          />
          <Detail label="Location" value={shift.location} />
          <Detail label="Pay Rate" value={`${formatMoney(shift.pay_rate, shift.currency)}/hr`} strong />
          <div className="schedule-detail">
            <span>Status & Capacity</span>
            <StatusBadge status={shift.status} variant="shift" />
            <p>
              {shift.workers_filled} of {shift.workers_needed} workers assigned
            </p>
          </div>
          {shift.notes && <Detail label="Notes" value={shift.notes} />}
          <Detail label="Created" value={formatDateTime(shift.created_at)} />
        </div>
      </section>
    </div>
  );
}

function Detail({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="schedule-detail">
      <span>{label}</span>
      <p className={strong ? "strong" : ""}>{value}</p>
    </div>
  );
}
