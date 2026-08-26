import { ReactNode, useEffect, useMemo, useState } from "react";

import { useAuth } from "../contexts/AuthContext";
import { fetchJson } from "../lib/api";
import { formatMoney } from "../lib/format";
import type { Application, Shift } from "../types/operations";
import "./AnalyticsPage.css";

export function AnalyticsPage() {
  const { user } = useAuth();
  const currency = user?.currency ?? "GBP";
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [shiftData, applicationData] = await Promise.all([
        fetchJson<Shift[]>("/shifts"),
        fetchJson<Application[]>("/applications"),
      ]);
      setShifts(shiftData);
      setApplications(applicationData);
      setError(null);
    } catch (err) {
      setShifts([]);
      setApplications([]);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const insights = useMemo(
    () => buildInsights(shifts, applications),
    [shifts, applications]
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">See the coverage, candidate interest, and staffed hours Venue OS is delivering.</p>
        </div>
        <button className="btn secondary" type="button" onClick={loadAnalytics}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="card error-card">
          <p className="status error">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="card">
          <p className="booking-meta">Loading analytics...</p>
        </div>
      ) : (
        <>
          <div className="dashboard-grid">
            <Metric token="FR" label="Fill Rate" value={`${insights.fillRate.toFixed(1)}%`}>
              {insights.filledShifts} of {insights.totalShifts} shifts filled
            </Metric>
            <Metric token="AP" label="Applications Received" value={String(insights.totalApplications)}>
              Across {insights.applicationShiftCount} {insights.applicationShiftCount === 1 ? "shift" : "shifts"}
            </Metric>
            <Metric token="HR" label="Staff Hours Booked" value={`${formatHours(insights.staffHoursBooked)}h`}>
              {insights.filledPositions} filled {insights.filledPositions === 1 ? "position" : "positions"}
            </Metric>
            <Metric token="$" label="Avg Pay Rate" value={formatMoney(insights.avgPayRate, currency)}>
              Per hour across all shifts
            </Metric>
          </div>

          <div className="workspace">
            <DayOfWeekChart counts={insights.dayOfWeekCounts} />
            <TopRoles roles={insights.topRoles} />
          </div>

          <PerformanceInsights insights={insights} />
        </>
      )}
    </div>
  );
}

function Metric({
  token,
  label,
  value,
  children,
}: {
  token: string;
  label: string;
  value: string;
  children: ReactNode;
}) {
  return (
    <div className="metric-card card">
      <div className="metric-header">
        <span className="metric-icon" aria-hidden="true">{token}</span>
        <h3 className="metric-label">{label}</h3>
      </div>
      <p className="metric-value">{value}</p>
      <p className="metric-change">{children}</p>
    </div>
  );
}

function DayOfWeekChart({ counts }: { counts: number[] }) {
  const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const maxCount = Math.max(...counts, 1);

  return (
    <div className="card" style={{ padding: "24px" }}>
      <h3 style={{ margin: "0 0 20px" }}>Popular Shift Times</h3>
      <div style={{ display: "grid", gap: "12px" }}>
        {daysOfWeek.map((day, index) => {
          const count = counts[index];
          const percentage = (count / maxCount) * 100;
          return (
            <div key={day}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>{day}</span>
                <span style={{ fontSize: "0.9rem", color: "var(--ink-500)" }}>
                  {count} {count === 1 ? "shift" : "shifts"}
                </span>
              </div>
              <div style={{ height: "8px", background: "rgba(15, 23, 32, 0.08)", borderRadius: "4px", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${percentage}%`,
                    background: "linear-gradient(90deg, var(--ocean-500), var(--ocean-300))",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TopRoles({ roles }: { roles: [string, number][] }) {
  return (
    <div className="card" style={{ padding: "24px" }}>
      <h3 style={{ margin: "0 0 20px" }}>Top Roles</h3>
      {roles.length === 0 ? (
        <p className="booking-meta">No shift data yet</p>
      ) : (
        <div style={{ display: "grid", gap: "12px" }}>
          {roles.map(([role, count], index) => (
            <div key={role} className="application-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>#{index + 1} {role}</strong>
                <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--ocean-500)" }}>
                  {count}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PerformanceInsights({ insights }: { insights: AnalyticsInsights }) {
  const items = [
    insights.filledShifts > 0
      ? `${insights.filledShifts} ${insights.filledShifts === 1 ? "shift has" : "shifts have"} reached full coverage through Venue OS.`
      : null,
    insights.totalApplications > 0
      ? `${insights.totalApplications} ${insights.totalApplications === 1 ? "application has" : "applications have"} been received across ${insights.applicationShiftCount} ${insights.applicationShiftCount === 1 ? "shift" : "shifts"}.`
      : null,
    insights.staffHoursBooked > 0
      ? `${formatHours(insights.staffHoursBooked)} staff hours are booked across ${insights.filledPositions} filled ${insights.filledPositions === 1 ? "position" : "positions"}.`
      : null,
    insights.totalShifts > 0 && insights.totalApplications === 0
      ? "Your shifts are live. Candidate interest will appear here as applications arrive."
      : null,
    insights.totalShifts === 0
      ? "Create your first shift to start seeing analytics."
      : null,
  ].filter((item): item is string => Boolean(item));

  return (
    <div className="card" style={{ padding: "24px" }}>
      <h3 style={{ margin: "0 0 16px" }}>Performance Insights</h3>
      <div style={{ display: "grid", gap: "12px" }}>
        {items.map((item) => (
          <div key={item} className="application-card">
            <p className="booking-meta">{item}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

type AnalyticsInsights = ReturnType<typeof buildInsights>;

function buildInsights(shifts: Shift[], applications: Application[]) {
  const totalShifts = shifts.length;
  const filledShifts = shifts.filter((shift) => shift.status === "filled").length;
  const staffedShifts = shifts.filter((shift) => shift.status !== "cancelled");
  const filledPositions = staffedShifts.reduce((sum, shift) => sum + shift.workers_filled, 0);
  const staffHoursBooked = staffedShifts.reduce((sum, shift) => (
    sum + ((new Date(shift.end_time).getTime() - new Date(shift.start_time).getTime()) / 3_600_000) * shift.workers_filled
  ), 0);
  const applicationShiftCount = new Set(applications.map((application) => application.shift_id)).size;
  const roleCounts = shifts.reduce((accumulator, shift) => {
    accumulator[shift.role] = (accumulator[shift.role] || 0) + 1;
    return accumulator;
  }, {} as Record<string, number>);
  const dayOfWeekCounts = [0, 0, 0, 0, 0, 0, 0];
  shifts.forEach((shift) => {
    dayOfWeekCounts[new Date(shift.start_time).getDay()] += 1;
  });

  return {
    totalShifts,
    filledShifts,
    fillRate: totalShifts > 0 ? (filledShifts / totalShifts) * 100 : 0,
    totalApplications: applications.length,
    applicationShiftCount,
    filledPositions,
    staffHoursBooked,
    topRoles: Object.entries(roleCounts).sort(([, left], [, right]) => right - left).slice(0, 5),
    dayOfWeekCounts,
    avgPayRate: shifts.length > 0
      ? shifts.reduce((sum, shift) => sum + Number(shift.pay_rate), 0) / shifts.length
      : 0,
  };
}

function formatHours(hours: number) {
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 }).format(hours);
}
