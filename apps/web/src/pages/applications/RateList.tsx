import { useState } from "react";

import { EmptyState } from "../../components/EmptyState";
import { stars } from "../../components/WorkerRail";
import { initials } from "../../lib/useVenue";
import type { CompletedShift, WorkerProfile } from "../../types/operations";
import { shortDay } from "../dashboard/dashboardUtils";
import { RatingModal } from "../workers/RatingModal";

type RateListProps = {
  shifts: CompletedShift[];
  workers: Record<string, WorkerProfile>;
  onRated: () => Promise<unknown>;
};

export function RateList({ shifts, workers, onRated }: RateListProps) {
  const [target, setTarget] = useState<CompletedShift | null>(null);

  if (shifts.length === 0) {
    return (
      <EmptyState
        title="Nothing to rate"
        message="After a shift is finished and the hours are approved, the worker appears here for a quick star rating."
      />
    );
  }

  return (
    <section className="ap-group">
      {shifts.map((shift) => {
        const name = workers[shift.worker_id]?.display_name || "Worker";
        return (
          <div key={shift.booking_id} className="ap-row">
            <span className="ap-avatar">{initials(name)}</span>
            <div className="ap-who">
              <b>{name}</b>
              <span className="ap-evidence">
                {shift.role} · {shift.location} · {shortDay(shift.start_time)}
              </span>
            </div>
            <div className="ap-acts">
              {shift.operator_rating === null ? (
                <button type="button" className="btn primary compact" onClick={() => setTarget(shift)}>
                  Rate {name.split(" ")[0]}
                </button>
              ) : (
                <span className="ap-rated">{stars(shift.operator_rating)}</span>
              )}
            </div>
          </div>
        );
      })}

      {target && (
        <RatingModal
          rating={{
            booking_id: target.booking_id,
            shift_id: target.shift_id,
            target_id: target.worker_id,
            target_name: workers[target.worker_id]?.display_name ?? "Worker",
            target_avatar_url: undefined,
            shift_role: target.role,
            shift_location: target.location,
            start_time: target.start_time,
            end_time: target.start_time,
          }}
          onDone={async () => {
            setTarget(null);
            await onRated();
          }}
          onClose={() => setTarget(null)}
        />
      )}
    </section>
  );
}
