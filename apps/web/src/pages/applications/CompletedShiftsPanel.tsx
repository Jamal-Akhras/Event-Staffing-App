import { useState } from "react";

import type { WorkerProfile } from "../../types/operations";
import { RatingModal } from "../workers/RatingModal";

export type CompletedShift = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  start_time: string;
  role: string;
  location: string;
  operator_rating: number | null;
};

type CompletedShiftsPanelProps = {
  shifts: CompletedShift[];
  workersById: Record<string, WorkerProfile>;
  onRated: () => Promise<void>;
};

export function CompletedShiftsPanel({ shifts, workersById, onRated }: CompletedShiftsPanelProps) {
  const [target, setTarget] = useState<CompletedShift | null>(null);
  if (shifts.length === 0) return null;

  return (
    <div className="panel card">
      <div className="panel-title"><h3>Completed Shifts</h3><span className="pill">{shifts.length}</span></div>
      <div className="recent-list">
        {shifts.map((shift) => (
          <div key={shift.booking_id} className="application-card completed-shift-card">
            <div>
              <p className="booking-id">{shift.role}</p>
              <p className="booking-meta">{shift.location}</p>
              <p className="booking-meta">{new Date(shift.start_time).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}</p>
            </div>
            {shift.operator_rating !== null ? (
              <span className="completed-shift-stars">{"★".repeat(shift.operator_rating)}{"☆".repeat(5 - shift.operator_rating)}</span>
            ) : (
              <button className="btn secondary compact" type="button" onClick={() => setTarget(shift)}>Rate worker</button>
            )}
          </div>
        ))}
      </div>
      {target && (
        <RatingModal
          rating={{
            booking_id: target.booking_id,
            shift_id: target.shift_id,
            target_id: target.worker_id,
            target_name: workersById[target.worker_id]?.display_name ?? target.worker_id,
            target_avatar_url: undefined,
            shift_role: target.role,
            shift_location: target.location,
            start_time: target.start_time,
            end_time: target.start_time,
          }}
          onDone={async () => { setTarget(null); await onRated(); }}
          onClose={() => setTarget(null)}
        />
      )}
    </div>
  );
}
