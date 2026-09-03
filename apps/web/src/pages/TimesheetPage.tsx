import { useEffect, useState } from "react";

import { ErrorCard } from "../components/ErrorCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { readWeekStart } from "../lib/weekStart";
import { useVenue } from "../lib/useVenue";
import { toVenueWallDate } from "../lib/venueTime";
import type { TimesheetDay } from "../types/rota";
import { boardDays, boardLabel, isoDay, shiftDays, weekStartFor } from "./shifts/boardUtils";
import { AdjustHoursModal, CorrectChargeModal } from "./timesheet/AdjustHoursModal";
import { TimesheetTable } from "./timesheet/TimesheetTable";
import { useTimesheet } from "./timesheet/useTimesheet";
import "./TimesheetPage.css";

type ModalState =
  | { kind: "adjust" | "record"; day: TimesheetDay }
  | { kind: "correct"; day: TimesheetDay }
  | null;

export function TimesheetPage() {
  const { toast } = useToast();
  const venue = useVenue();
  const timezone = venue.data?.timezone ?? null;
  const [anchor, setAnchor] = useState<Date | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [modal, setModal] = useState<ModalState>(null);

  useEffect(() => {
    if (timezone) setAnchor(toVenueWallDate(new Date(), timezone));
  }, [timezone]);

  const calendarAnchor = anchor ?? new Date(0);
  const days = boardDays(weekStartFor(calendarAnchor, readWeekStart()));
  const weekStart = isoDay(days[0]);
  const currency = venue.data?.currency ?? "GBP";
  const notify = (type: "success" | "error", message: string) => toast({ type, message });
  const timesheet = useTimesheet(weekStart, notify, timezone !== null);

  useEffect(() => {
    setSelected(new Set());
    setModal(null);
  }, [weekStart]);

  if (venue.error) return <ErrorCard message={(venue.error as Error).message} />;
  if (!venue.data || !anchor) return <SkeletonCard lines={8} />;
  if (!timezone) return <ErrorCard message="Choose a venue market before opening timesheets." />;

  const toggle = (bookingId: string) =>
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(bookingId)) next.delete(bookingId);
      else next.add(bookingId);
      return next;
    });

  const approveSelected = () => {
    timesheet.approve.mutate([...selected], { onSuccess: () => setSelected(new Set()) });
  };

  const workerName = (day: TimesheetDay) =>
    timesheet.week.data?.workers.find((worker) => worker.days.some((row) => row.booking_id === day.booking_id))
      ?.display_name ?? "Worker";

  return (
    <div className="ts-page">
      <div className="ts-header">
        <div className="bd-nav">
          <button type="button" className="bd-nav-arrow" aria-label="Previous week" onClick={() => setAnchor(shiftDays(anchor, -7))}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M15 6l-6 6 6 6" />
            </svg>
          </button>
          <button type="button" className="bd-nav-today" onClick={() => setAnchor(toVenueWallDate(new Date(), timezone))}>This week</button>
          <button type="button" className="bd-nav-arrow" aria-label="Next week" onClick={() => setAnchor(shiftDays(anchor, 7))}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9 6l6 6-6 6" />
            </svg>
          </button>
        </div>
        <h1 className="bd-title">Timesheet · {boardLabel(days)}</h1>
        <div className="ts-header-actions">
          <button type="button" className="ov-btn" onClick={timesheet.download}>Download CSV</button>
          <button
            type="button"
            className="ov-btn ov-btn-primary"
            disabled={selected.size === 0 || timesheet.approve.isPending}
            onClick={approveSelected}
          >
            {timesheet.approve.isPending ? "Approving..." : `Approve selected${selected.size > 0 ? ` (${selected.size})` : ""}`}
          </button>
        </div>
      </div>

      {timesheet.week.error ? (
        <ErrorCard message={(timesheet.week.error as Error).message} />
      ) : !timesheet.week.data ? (
        <SkeletonCard lines={8} />
      ) : (
        <TimesheetTable
          week={timesheet.week.data}
          currency={currency}
          timezone={timezone}
          selected={selected}
          onToggle={toggle}
          onAdjust={(day) => setModal({ kind: "adjust", day })}
          onRecord={(day) => setModal({ kind: "record", day })}
          onCorrect={(day) => setModal({ kind: "correct", day })}
        />
      )}

      {modal && modal.kind !== "correct" && (
        <AdjustHoursModal
          day={modal.day}
          workerName={workerName(modal.day)}
          mode={modal.kind}
          timezone={timezone}
          busy={timesheet.adjust.isPending || timesheet.recordAttendance.isPending}
          onClose={() => setModal(null)}
          onSubmit={(payload) => {
            const done = { onSuccess: () => setModal(null) };
            if (modal.kind === "adjust") {
              timesheet.adjust.mutate({ bookingId: modal.day.booking_id, ...payload }, done);
            } else {
              timesheet.recordAttendance.mutate(
                { bookingId: modal.day.booking_id, checkedIn: payload.checkedIn, checkedOut: payload.checkedOut },
                done
              );
            }
          }}
        />
      )}
      {modal && modal.kind === "correct" && modal.day.charge_id && (
        <CorrectChargeModal
          day={modal.day}
          workerName={workerName(modal.day)}
          busy={timesheet.correct.isPending}
          onClose={() => setModal(null)}
          onSubmit={(payload) =>
            timesheet.correct.mutate(
              { chargeId: modal.day.charge_id as string, ...payload },
              { onSuccess: () => setModal(null) }
            )
          }
        />
      )}
    </div>
  );
}
