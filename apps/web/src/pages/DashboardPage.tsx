import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorCard } from "../components/ErrorCard";
import { Icon } from "../components/Icon";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { fetchJson } from "../lib/api";
import type { Application, Shift } from "../types/operations";
import { CoverageStrip } from "./dashboard/CoverageStrip";
import { MetricGrid } from "./dashboard/MetricGrid";
import { OpenShiftList } from "./dashboard/OpenShiftList";
import {
  buildCoverageDays,
  buildDashboardMetrics,
  getRecentOpenShifts,
} from "./dashboard/dashboardUtils";
import "./DashboardPage.css";

export function DashboardPage() {
  const { toast } = useToast();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
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
      toast({ type: "error", message: (err as Error).message });
      setShifts([]);
      setApplications([]);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const now = useMemo(() => new Date(), [shifts, applications]);
  const metrics = useMemo(
    () => buildDashboardMetrics(shifts, applications, now),
    [shifts, applications, now]
  );
  const coverageDays = useMemo(
    () => buildCoverageDays(shifts, now),
    [shifts, now]
  );
  const openShifts = useMemo(
    () => getRecentOpenShifts(shifts, now),
    [shifts, now]
  );
  const pendingReviewCount = useMemo(
    () => applications.filter((app) => app.status === "applied").length,
    [applications]
  );
  const openSeatCount = useMemo(() => getOpenSeatCount(shifts), [shifts]);
  const attentionCount = pendingReviewCount + openSeatCount;
  const alert = getDashboardAlert(pendingReviewCount, openSeatCount);
  const initialLoading = loading && shifts.length === 0 && applications.length === 0 && !error;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">{formatDashboardDate(now)}</p>
        </div>
        <button className="btn secondary" type="button" onClick={loadDashboard}>
          <Icon name="refresh" size={16} />
          Refresh
        </button>
      </div>

      {initialLoading ? (
        <DashboardSkeleton />
      ) : error ? (
        <ErrorCard message={error} />
      ) : (
        <>
          <section className={`dashboard-alert ${attentionCount === 0 ? "clear" : ""}`}>
            <span className="attention-hero-icon">
              <Icon name={attentionCount === 0 ? "check" : "alert-triangle"} size={24} />
            </span>
            <div className="attention-hero-copy">
              <strong>{alert.title}</strong>
              <p>{alert.note}</p>
            </div>
            <Link className="btn primary" to={alert.to}>
              {alert.action}
            </Link>
          </section>

          <MetricGrid metrics={metrics} loading={loading} />

          <CoverageStrip days={coverageDays} />

          <div className="dashboard-workspace">
            <OpenShiftList shifts={openShifts} />
            <QuickActions />
          </div>
        </>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <>
      <div className="dashboard-grid">
        {Array.from({ length: 4 }, (_, index) => <SkeletonCard key={index} variant="metric" />)}
      </div>
      <div className="dashboard-workspace dashboard-skeleton-workspace">
        <SkeletonCard className="dashboard-skeleton-wide" lines={5} />
        <SkeletonCard className="dashboard-skeleton-wide" lines={4} />
      </div>
      <div className="dashboard-skeleton-strip">
        {Array.from({ length: 7 }, (_, index) => <SkeletonCard key={index} variant="row" lines={2} />)}
      </div>
    </>
  );
}

function getOpenSeatCount(shifts: Shift[]) {
  return shifts.reduce(
    (sum, shift) => sum + Math.max(shift.workers_needed - shift.workers_filled, 0),
    0
  );
}

function formatDashboardDate(value: Date) {
  return value.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function getDashboardAlert(pendingReviews: number, openSeats: number) {
  if (pendingReviews > 0) {
    return {
      title: `${pendingReviews} pending applications`,
      note: `${openSeats} open seats across active shifts. Review workers before the next service window.`,
      to: "/app/applications",
      action: "Review now",
    };
  }

  if (openSeats > 0) {
    return {
      title: `${openSeats} open seats`,
      note: "Coverage is still incomplete across active shifts.",
      to: "/app/schedule",
      action: "View schedule",
    };
  }

  return {
    title: "No urgent staffing actions",
    note: "Coverage and application queues are clear right now.",
    to: "/app/shifts",
    action: "Post shift",
  };
}

function QuickActions() {
  return (
    <section className="card quick-actions-panel">
      <div className="dashboard-section-header">
        <div>
          <h2>Quick Actions</h2>
          <p>Common venue-manager workflows.</p>
        </div>
      </div>

      <div className="quick-action-list">
        <Link to="/app/shifts">
          <strong>Post coverage</strong>
          <p>Create a shift or refresh open staffing needs.</p>
        </Link>
        <Link to="/app/templates">
          <strong>Use a template</strong>
          <p>Generate repeatable shifts without retyping details.</p>
        </Link>
        <Link to="/app/applications">
          <strong>Review applicants</strong>
          <p>Compare reliability, fit, and application history.</p>
        </Link>
      </div>
    </section>
  );
}
