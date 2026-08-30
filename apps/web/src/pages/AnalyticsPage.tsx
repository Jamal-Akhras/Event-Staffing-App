import { useState } from "react";

import { ErrorCard } from "../components/ErrorCard";
import { PageHeader } from "../components/PageHeader";
import { SkeletonCard } from "../components/SkeletonCard";
import { formatMoney } from "../lib/format";
import { useVenueAnalytics } from "../lib/useInsights";
import type { AnalyticsPeriod } from "../types/insights";
import { GapList, RoleList } from "./analytics/GapList";
import { MetricCard } from "./analytics/MetricCard";
import "./AnalyticsPage.css";

const PERIODS: { key: AnalyticsPeriod; label: string }[] = [
  { key: "week", label: "Week" },
  { key: "month", label: "Month" },
  { key: "quarter", label: "Quarter" },
];

const LEAD: Record<AnalyticsPeriod, string> = {
  week: "Coverage, interest and cost across the last seven days.",
  month: "Coverage, interest and cost across the last thirty days.",
  quarter: "Coverage, interest and cost across the last quarter.",
};

export function AnalyticsPage() {
  const [period, setPeriod] = useState<AnalyticsPeriod>("month");
  const analytics = useVenueAnalytics(period);

  if (analytics.error) return <ErrorCard message={(analytics.error as Error).message} />;

  const data = analytics.data;

  return (
    <div className="pg">
      <PageHeader
        title="Analytics"
        lead={LEAD[period]}
        emphasis={
          data && data.gaps.length > 0
            ? `${data.gaps.reduce((sum, gap) => sum + gap.unfilled, 0)} seats went unfilled.`
            : data
              ? "Every seat you posted was covered."
              : undefined
        }
        actions={
          <div className="an-period" role="tablist" aria-label="Period">
            {PERIODS.map((item) => (
              <button
                key={item.key}
                type="button"
                role="tab"
                aria-selected={period === item.key}
                className={period === item.key ? "on" : ""}
                onClick={() => setPeriod(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        }
      />

      {!data ? (
        <>
          <SkeletonCard lines={2} />
          <SkeletonCard lines={5} />
        </>
      ) : (
        <>
          <div className="an-metrics">
            <MetricCard
              label="Fill rate"
              value={`${data.fill_rate}%`}
              note={`${data.seats_filled} of ${data.seats_posted} seats`}
              trend={data.fill_rate_trend}
            />
            <MetricCard
              label="Applications"
              value={String(data.applications)}
              note={`${data.applications_per_seat} per seat`}
              trend={data.applications_trend}
            />
            <MetricCard
              label="Hours staffed"
              value={String(Math.round(Number(data.hours_staffed)))}
              note="Excludes cancelled shifts"
              trend={data.hours_trend}
            />
            <MetricCard
              label="Average rate"
              value={formatMoney(data.average_pay_rate, data.currency)}
              note="Per hour across posted shifts"
              trend={data.rate_trend}
            />
          </div>

          <div className="an-row">
            <GapList gaps={data.gaps} />
            <RoleList roles={data.roles} />
          </div>
        </>
      )}
    </div>
  );
}
