import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ErrorCard } from "../components/ErrorCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { track } from "../lib/analytics";
import { useVenue } from "../lib/useVenue";
import { readWeekStart, saveWeekStart } from "../lib/weekStart";
import type { Shift } from "../types/operations";
import type { Template } from "../types/templates";
import { DecisionList } from "./dashboard/DecisionList";
import { StatRow } from "./dashboard/StatRow";
import { completedCounts, describeOldest, sortedPending, tonightRows } from "./dashboard/dashboardUtils";
import { useDecideApplication } from "./dashboard/useOverviewData";
import { BoardHeader } from "./shifts/BoardHeader";
import { PostShiftModal, type PostDraft } from "./shifts/PostShiftModal";
import { ShiftManagementModal } from "./shifts/ShiftManagementModal";
import { TemplateChips } from "./shifts/TemplateChips";
import { TonightRail } from "./shifts/TonightRail";
import { WeekBoard } from "./shifts/WeekBoard";
import { boardDays, defaultStartFor, missingSeats, shiftDays, weekStartFor } from "./shifts/boardUtils";
import { useBoardData } from "./shifts/useBoardData";
import "./DashboardPage.css";
import "./dashboard/OverviewCards.css";
import "./ShiftsPage.css";

export function ShiftsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const venue = useVenue();
  const now = new Date();
  const decide = useDecideApplication(
    (message) => toast({ type: "success", message }),
    (message) => toast({ type: "error", message })
  );
  const [weekStart, setWeekStart] = useState(readWeekStart);
  const [anchor, setAnchor] = useState(() => new Date());
  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [selected, setSelected] = useState<Shift | null>(null);

  const days = boardDays(weekStartFor(anchor, weekStart));
  const data = useBoardData(days, now);
  const location = venue.data?.default_location ?? "";
  const currency = venue.data?.currency ?? "GBP";
  const weekShifts = data.shifts.filter((shift) => shift.status !== "cancelled");
  const openSeats = weekShifts.reduce((sum, shift) => sum + missingSeats(shift), 0);
  const openShifts = weekShifts.filter((shift) => missingSeats(shift) > 0).length;
  const bookedSeats = weekShifts.reduce((sum, shift) => sum + shift.workers_filled, 0);
  const postedSeats = weekShifts.reduce((sum, shift) => sum + shift.workers_needed, 0);
  const pending = sortedPending(data.applications.filter((application) => application.status === "applied"));

  const refresh = async () => {
    await Promise.all(["shifts", "applications", "bookings"].map((key) => queryClient.invalidateQueries({ queryKey: [key] })));
  };

  const changeWeekStart = (day: number) => {
    saveWeekStart(day);
    setWeekStart(day);
  };

  const postFromTemplate = (template: Template) =>
    setDraft({
      initial: {
        role: template.role,
        location: template.location,
        pay_rate: String(template.pay_rate),
        workers_needed: String(template.workers_needed),
        notes: template.notes ?? "",
      },
      durationHours: template.duration_hours,
    });

  return (
    <div className="board-page">
      <div className="board-main">
        <BoardHeader
          days={days}
          openSeats={openSeats}
          weekStart={weekStart}
          onWeekStartChange={changeWeekStart}
          onPrevious={() => setAnchor(shiftDays(anchor, -7))}
          onToday={() => setAnchor(new Date())}
          onNext={() => setAnchor(shiftDays(anchor, 7))}
          onPost={() => setDraft({ initial: { location } })}
        />
        <TemplateChips currency={currency} onPick={postFromTemplate} />
        {data.error ? (
          <ErrorCard message={data.error.message} />
        ) : data.loading ? (
          <SkeletonCard lines={8} />
        ) : (
          <>
            <WeekBoard
              days={days}
              shifts={data.shifts}
              applications={data.applications}
              now={now}
              onAdd={(day) => setDraft({ initial: { location, start_time: defaultStartFor(day) } })}
              onSelect={(shift) => {
                track("shift.opened", { subject_type: "shift", subject_id: shift.shift_id, context: { status: shift.status } });
                setSelected(shift);
              }}
            />
            <div className="bd-summary">
              <StatRow
                stats={[
                  { label: "Shifts this week", value: String(weekShifts.length), note: `${weekShifts.length - openShifts} filled · ${openShifts} still open` },
                  { label: "Open seats", value: String(openSeats), note: openSeats > 0 ? "Across the shifts marked open" : "Everything is covered", tone: openSeats > 0 ? "warning" : "success" },
                  { label: "Booked seats", value: `${bookedSeats} of ${postedSeats}`, note: "Workers confirmed against seats posted" },
                  {
                    label: "Applications waiting",
                    value: String(data.overview?.pending_applications.count ?? 0),
                    note: describeOldest(data.overview?.pending_applications.oldest_created_at ?? null, now),
                  },
                ]}
              />
            </div>
          </>
        )}
      </div>

      <aside className="board-rail">
        <DecisionList
          pending={pending}
          shifts={data.shifts}
          workers={data.workers}
          completedCounts={completedCounts(data.activity)}
          busyId={decide.isPending ? decide.variables?.applicationId ?? null : null}
          onDecide={(applicationId, action) => decide.mutate({ applicationId, action })}
        />
        <TonightRail rows={tonightRows(data.overview?.tonight ?? [], data.workers)} />
      </aside>

      {draft && (
        <PostShiftModal
          draft={draft}
          onClose={() => setDraft(null)}
          onError={(message) => toast({ type: "error", message })}
          onCreated={async () => {
            setDraft(null);
            await refresh();
            toast({ type: "success", message: "Shift posted." });
          }}
        />
      )}
      {selected && (
        <ShiftManagementModal
          shift={selected}
          bookings={data.bookings}
          workers={data.workers}
          onChanged={refresh}
          onClose={() => setSelected(null)}
          onSaved={async (message) => {
            setSelected(null);
            await refresh();
            toast({ type: "success", message });
          }}
        />
      )}
    </div>
  );
}
