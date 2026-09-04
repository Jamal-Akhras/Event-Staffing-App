import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ErrorCard } from "../components/ErrorCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { track } from "../lib/analytics";
import { useVenue } from "../lib/useVenue";
import { toVenueWallDate } from "../lib/venueTime";
import { readWeekStart, saveWeekStart } from "../lib/weekStart";
import type { Shift } from "../types/operations";
import type { Template } from "../types/templates";
import { DecisionList } from "./dashboard/DecisionList";
import { StatRow } from "./dashboard/StatRow";
import { completedCounts, describeOldest, sortedPending, tonightRows } from "./dashboard/dashboardUtils";
import { useDecideApplication } from "./dashboard/useOverviewData";
import { BoardHeader } from "./shifts/BoardHeader";
import { ContractedStrip } from "./shifts/ContractedStrip";
import { PostShiftModal, type PostDraft } from "./shifts/PostShiftModal";
import { PublishBar } from "./shifts/PublishBar";
import { ShiftManagementModal } from "./shifts/ShiftManagementModal";
import { TemplateChips } from "./shifts/TemplateChips";
import { ChangeRequestQueue } from "./shifts/ChangeRequestQueue";
import { TimeOffQueue } from "./shifts/TimeOffQueue";
import { TonightRail } from "./shifts/TonightRail";
import { WeekBoard } from "./shifts/WeekBoard";
import {
  boardDays,
  defaultStartFor,
  isoDay,
  missingSeats,
  projectedCost,
  scheduledHoursByWorker,
  shiftDays,
  weekStartFor,
} from "./shifts/boardUtils";
import { useBoardData } from "./shifts/useBoardData";
import { usePublications, useRotaActions } from "./shifts/useRota";
import { useChangeRequests } from "./shifts/useChangeRequests";
import { useTimeOffQueue } from "./shifts/useTimeOffQueue";
import { usePeople } from "./workers/useDirectory";
import "./DashboardPage.css";
import "./dashboard/OverviewCards.css";
import "./ShiftsPage.css";

export function ShiftsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const venue = useVenue();
  const timezone = venue.data?.timezone ?? null;
  const instantNow = new Date();
  const now = timezone ? toVenueWallDate(instantNow, timezone) : new Date(0);
  const decide = useDecideApplication(
    (message) => toast({ type: "success", message }),
    (message) => toast({ type: "error", message })
  );
  const [weekStart, setWeekStart] = useState(readWeekStart);
  const [anchor, setAnchor] = useState<Date | null>(null);
  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [selected, setSelected] = useState<Shift | null>(null);

  useEffect(() => {
    if (timezone) setAnchor(toVenueWallDate(new Date(), timezone));
  }, [timezone]);

  const calendarAnchor = anchor ?? new Date(0);
  const days = boardDays(weekStartFor(calendarAnchor, weekStart));
  const weekKey = isoDay(days[0]);
  const data = useBoardData(days, now, timezone);
  const people = usePeople();
  const publications = usePublications(weekKey, timezone !== null);
  const rota = useRotaActions(weekKey, (type, message) => toast({ type, message }));
  const timeOff = useTimeOffQueue((type, message) => toast({ type, message }));
  const changes = useChangeRequests((type, message) => toast({ type, message }));
  const location = venue.data?.default_location ?? "";
  const currency = venue.data?.currency ?? "GBP";
  const peopleNames = Object.fromEntries(
    (people.data ?? []).map((entry) => [entry.worker_id, entry.display_name])
  );
  const weekShifts = data.shifts.filter((shift) => shift.status !== "cancelled");
  const openSeats = weekShifts.reduce((sum, shift) => sum + missingSeats(shift), 0);
  const openShifts = weekShifts.filter((shift) => missingSeats(shift) > 0).length;
  const bookedSeats = weekShifts.reduce((sum, shift) => sum + shift.workers_filled, 0);
  const postedSeats = weekShifts.reduce((sum, shift) => sum + shift.workers_needed, 0);
  const draftCount = weekShifts.filter((shift) => shift.rota_state === "draft").length;
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

  if (venue.error) return <ErrorCard message={(venue.error as Error).message} />;
  if (!venue.data || !anchor) return <SkeletonCard lines={8} />;
  if (!timezone) return <ErrorCard message="Choose a venue market before building the rota." />;

  return (
    <div className="board-page">
      <div className="board-main">
        <BoardHeader
          days={days}
          openSeats={openSeats}
          filledSeats={bookedSeats}
          postedSeats={postedSeats}
          projected={projectedCost(weekShifts)}
          currency={currency}
          draftCount={draftCount}
          publishing={rota.publish.isPending}
          weekStart={weekStart}
          onWeekStartChange={changeWeekStart}
          onPrevious={() => setAnchor(shiftDays(anchor, -7))}
          onToday={() => setAnchor(toVenueWallDate(new Date(), timezone))}
          onNext={() => setAnchor(shiftDays(anchor, 7))}
          onPost={() => setDraft({ initial: { location } })}
          onPublish={() => rota.publish.mutate()}
        />
        <TemplateChips currency={currency} onPick={postFromTemplate} />
        {data.error ? (
          <ErrorCard message={data.error.message} />
        ) : data.loading ? (
          <SkeletonCard lines={8} />
        ) : (
          <>
            <PublishBar publications={publications.data ?? []} people={peopleNames} />
            <WeekBoard
              days={days}
              shifts={data.shifts}
              applications={data.applications}
              people={peopleNames}
              currency={currency}
              now={now}
              timezone={timezone}
              onAdd={(day) => setDraft({ initial: { location, start_time: defaultStartFor(day) } })}
              onSelect={(shift) => {
                track("shift.opened", { subject_type: "shift", subject_id: shift.shift_id, context: { status: shift.status } });
                setSelected(shift);
              }}
            />
            <ContractedStrip entries={people.data ?? []} scheduled={scheduledHoursByWorker(weekShifts)} />
            <div className="bd-summary">
              <StatRow
                stats={[
                  { label: "Shifts this week", value: String(weekShifts.length), note: `${weekShifts.length - openShifts} filled · ${openShifts} still open` },
                  { label: "Open seats", value: String(openSeats), note: openSeats > 0 ? "Across the shifts marked open" : "Everything is covered", tone: openSeats > 0 ? "warning" : "success" },
                  { label: "Booked seats", value: `${bookedSeats} of ${postedSeats}`, note: "Workers confirmed against seats posted" },
                  {
                    label: "Applications waiting",
                    value: String(data.overview?.pending_applications.count ?? 0),
                    note: describeOldest(data.overview?.pending_applications.oldest_created_at ?? null, instantNow),
                  },
                ]}
              />
            </div>
          </>
        )}
      </div>

      <aside className="board-rail">
        <TimeOffQueue
          requests={timeOff.query.data ?? []}
          people={peopleNames}
          timezone={timezone}
          loading={timeOff.query.isLoading}
          error={timeOff.query.error as Error | null}
          busyId={timeOff.decision.isPending ? timeOff.decision.variables?.requestId ?? null : null}
          onDecide={(requestId, action) => timeOff.decision.mutate({ requestId, action })}
        />
        <ChangeRequestQueue
          requests={changes.query.data ?? []}
          people={peopleNames}
          timezone={timezone}
          loading={changes.query.isLoading}
          error={changes.query.error as Error | null}
          busyId={changes.decision.isPending ? changes.decision.variables?.requestId ?? null : null}
          onDecide={(requestId, action) => changes.decision.mutate({ requestId, action })}
        />
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
          timezone={timezone}
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
          timezone={timezone}
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
