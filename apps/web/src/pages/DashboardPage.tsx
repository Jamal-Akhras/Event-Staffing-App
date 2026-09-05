import { ErrorCard } from "../components/ErrorCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { useVenue } from "../lib/useVenue";
import { DecisionList } from "./dashboard/DecisionList";
import { OverviewHeader } from "./dashboard/OverviewHeader";
import { RegularsCard } from "./dashboard/RegularsCard";
import { StatRow } from "./dashboard/StatRow";
import { TonightCard } from "./dashboard/TonightCard";
import { WeekStrip } from "./dashboard/WeekStrip";
import {
  completedCounts,
  coverageDays,
  describeOldest,
  describeOpenSeats,
  regulars,
  sortedPending,
  tonightRows,
} from "./dashboard/dashboardUtils";
import { useDecideApplication, useOverviewData } from "./dashboard/useOverviewData";
import "./DashboardPage.css";
import "./dashboard/OverviewCards.css";

export function DashboardPage() {
  const { toast } = useToast();
  const venue = useVenue();
  const now = new Date();
  const data = useOverviewData(now);
  const decide = useDecideApplication(
    (message) => toast({ type: "success", message }),
    (message) => toast({ type: "error", message })
  );

  if (data.error) {
    return <ErrorCard message={data.error.message} />;
  }
  if (data.loading || venue.isPending || !data.overview) {
    return <OverviewSkeleton />;
  }

  const overview = data.overview;
  const days = coverageDays(overview.days);
  const pending = sortedPending(data.pending);
  const turnout = overview.attendance;
  const tonight = tonightRows(overview.tonight, data.workers);
  const tonightMissing = tonight.reduce((sum, row) => sum + row.missing, 0);
  const tonightNeeded = overview.tonight.reduce((sum, row) => sum + row.shift.workers_needed, 0);
  const tonightCovered = tonightNeeded - tonightMissing;
  const nextGap = days.slice(1).find((day) => day.openSeats > 0);
  const openSeats = overview.open_seats;

  const lead = tonight.length === 0
    ? "No shifts tonight."
    : tonightMissing > 0
      ? `Tonight still needs ${tonightMissing}.`
      : "Tonight is fully covered.";
  const emphasis = nextGap ? `${nextGap.longLabel} still needs ${nextGap.openSeats}.` : "The rest of the week is covered.";

  return (
    <div className="overview">
      <OverviewHeader venueName={venue.data?.name ?? "team"} now={now} covered={tonightCovered} needed={tonightNeeded} lead={lead} emphasis={emphasis} />

      <StatRow
        stats={[
          {
            label: "Open seats this week",
            value: String(openSeats),
            note: describeOpenSeats(days),
            tone: openSeats > 0 ? "warning" : "success",
          },
          {
            label: "Applications to review",
            value: String(overview.pending_applications.count),
            note: describeOldest(overview.pending_applications.oldest_created_at, now),
          },
          {
            label: "Regulars turned up",
            value: turnout.rate === null ? "—" : `${turnout.rate}%`,
            note: turnout.total ? `Last 30 days · ${turnout.total} shifts` : "No completed shifts yet",
            tone: turnout.rate !== null && turnout.rate >= 90 ? "success" : undefined,
          },
        ]}
      />

      <div className="ov-grid">
        <div className="ov-column">
          <TonightCard rows={tonight} />
          <WeekStrip days={days} />
        </div>
        <div className="ov-column">
          <DecisionList
            pending={pending}
            shifts={overview.tonight.map((row) => row.shift)}
            workers={data.workers}
            completedCounts={completedCounts(data.activity)}
            busyId={decide.isPending ? decide.variables?.applicationId ?? null : null}
            onDecide={(applicationId, action) => decide.mutate({ applicationId, action })}
          />
          <RegularsCard regulars={regulars(data.activity, data.workers)} />
        </div>
      </div>
    </div>
  );
}

function OverviewSkeleton() {
  return (
    <div className="overview">
      <SkeletonCard lines={2} />
      <div className="ov-grid">
        <SkeletonCard lines={5} />
        <SkeletonCard lines={5} />
      </div>
    </div>
  );
}
