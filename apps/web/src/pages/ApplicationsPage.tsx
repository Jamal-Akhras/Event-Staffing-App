import { ReactNode, useEffect, useState } from "react";
import { Application, ApplicationReviewCard, MessageHistory, ShiftSummary, WorkerProfile } from "../components/ApplicationReviewCard";
import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { MessageThread } from "../components/MessageThread";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { WorkerProfilePanel } from "../components/WorkerProfilePanel";
import { RatingModal } from "./workers/RatingModal";

import { fetchJson, postJson } from "../lib/api";
import "./ApplicationsPage.css";

type CompletedShift = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  start_time: string;
  role: string;
  location: string;
  operator_rating: number | null;
};

export function ApplicationsPage() {
  const { toast } = useToast();
  const [applications, setApplications] = useState<Application[]>([]);
  const [shiftsById, setShiftsById] = useState<Record<string, ShiftSummary>>({});
  const [workersById, setWorkersById] = useState<Record<string, WorkerProfile>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<WorkerProfile | null>(null);
  const [messagingApplication, setMessagingApplication] = useState<Application | null>(null);
  const [messageHistory, setMessageHistory] = useState<Record<string, MessageHistory[]>>({});
  const [completedShifts, setCompletedShifts] = useState<CompletedShift[]>([]);
  const [ratingTarget, setRatingTarget] = useState<CompletedShift | null>(null);
  const [loading, setLoading] = useState(true);

  const loadApplications = async () => {
    setLoading(true);
    try {
      const [data, completed] = await Promise.all([
        fetchJson<Application[]>("/applications"),
        fetchJson<CompletedShift[]>("/accounts/me/completed-shifts").catch(() => [] as CompletedShift[]),
      ]);
      const [shiftMap, workerMap] = await Promise.all([loadShifts(data), loadWorkers(data)]);
      setApplications(data);
      setShiftsById(shiftMap);
      setWorkersById(workerMap);
      setCompletedShifts(completed);
      setLoadError(null);
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
      setApplications([]);
      setShiftsById({});
      setWorkersById({});
      setLoadError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const loadMessageHistory = async (applicationId: string) => {
    if (messageHistory[applicationId]) {
      setMessageHistory((previous) => {
        const next = { ...previous };
        delete next[applicationId];
        return next;
      });
      return;
    }
    try {
      const data = await fetchJson<MessageHistory[]>(`/applications/${applicationId}/message-history`);
      setMessageHistory((previous) => ({ ...previous, [applicationId]: data }));
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
    }
  };

  const decideApplication = async (applicationId: string, action: "approve" | "reject") => {
    try {
      await postJson(`/applications/${applicationId}/${action}`, { now: new Date().toISOString() });
      await loadApplications();
      toast({ type: "success", message: `Application ${action === "approve" ? "approved" : "rejected"}.` });
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const pendingApplications = applications
    .filter((app) => app.status === "applied")
    .sort(bySoonestStart);
  const decidedApplications = applications
    .filter((app) => app.status !== "applied")
    .sort(byNewestDecision);
  const initialLoading = loading && applications.length === 0 && !loadError;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Applications</h1>
          <p className="page-subtitle">Approve reliable workers with shift context</p>
        </div>
        <button className="btn secondary" type="button" onClick={loadApplications}>
          Refresh
        </button>
      </div>

      {initialLoading && (
        <div className="workspace">
          <SkeletonCard className="applications-skeleton-card" lines={5} />
          <SkeletonCard className="applications-skeleton-card" lines={5} />
        </div>
      )}
      {!initialLoading && loadError && <ErrorCard message={loadError} />}

      {!initialLoading && !loadError && <div className="workspace">
        <ApplicationColumn
          title="Pending Applications"
          count={pendingApplications.length}
          emptyTitle="No pending applications"
          emptyMessage="New applications will appear here with worker reliability and shift coverage context."
        >
          {pendingApplications.map((item) => renderApplicationCard(item, true))}
        </ApplicationColumn>

        <ApplicationColumn
          title="Decided Applications"
          count={decidedApplications.length}
          emptyTitle="No decided applications"
          emptyMessage="Approved and rejected applications will appear here for auditability."
        >
          {decidedApplications.map((item) => renderApplicationCard(item, false))}
        </ApplicationColumn>

        {completedShifts.length > 0 && (
          <ApplicationColumn
            title="Completed Shifts"
            count={completedShifts.length}
            emptyTitle=""
            emptyMessage=""
          >
            {completedShifts.map((shift) => (
              <div key={shift.booking_id} className="application-card" style={{ display: "grid", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <p className="booking-id" style={{ margin: 0 }}>{shift.role}</p>
                    <p className="booking-meta" style={{ margin: "2px 0 0" }}>{shift.location}</p>
                    <p className="booking-meta">{new Date(shift.start_time).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}</p>
                  </div>
                  {shift.operator_rating !== null ? (
                    <span style={{ color: "#F59E0B", fontWeight: 800, fontSize: "1.1rem" }}>
                      {"★".repeat(shift.operator_rating)}{"☆".repeat(5 - shift.operator_rating)}
                    </span>
                  ) : (
                    <button
                      className="btn secondary"
                      style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                      type="button"
                      onClick={() => setRatingTarget(shift)}
                    >
                      Rate worker
                    </button>
                  )}
                </div>
              </div>
            ))}
          </ApplicationColumn>
        )}
      </div>}

      {selectedProfile && <WorkerProfilePanel profile={selectedProfile} onClose={() => setSelectedProfile(null)} />}

      {messagingApplication && <MessageModal application={messagingApplication} onClose={() => setMessagingApplication(null)} />}

      {ratingTarget && (
        <RatingModal
          bookingId={ratingTarget.booking_id}
          workerName={workersById[ratingTarget.worker_id]?.display_name ?? ratingTarget.worker_id}
          shiftRole={ratingTarget.role}
          shiftLocation={ratingTarget.location}
          shiftDate={new Date(ratingTarget.start_time).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}
          onDone={() => { setRatingTarget(null); loadApplications(); }}
          onClose={() => setRatingTarget(null)}
        />
      )}
    </div>
  );

  function renderApplicationCard(item: Application, decisionMode: boolean) {
    return (
      <ApplicationReviewCard
        key={item.application_id}
        application={item}
        shift={shiftsById[item.shift_id]}
        worker={workersById[item.worker_id]}
        messageHistory={messageHistory[item.application_id]}
        decisionMode={decisionMode}
        onApprove={() => decideApplication(item.application_id, "approve")}
        onReject={() => decideApplication(item.application_id, "reject")}
        onMessage={() => setMessagingApplication(item)}
        onViewProfile={() => setSelectedProfile(workersById[item.worker_id])}
        onToggleHistory={() => loadMessageHistory(item.application_id)}
      />
    );
  }
}

function ApplicationColumn({
  title,
  count,
  emptyTitle,
  emptyMessage,
  children,
}: {
  title: string;
  count: number;
  emptyTitle: string;
  emptyMessage: string;
  children: ReactNode;
}) {
  return (
    <div className="panel card">
      <div className="panel-title">
        <h3>{title}</h3>
        <span className="pill">{count}</span>
      </div>
      {count === 0 ? (
        <EmptyState title={emptyTitle} message={emptyMessage} />
      ) : (
        <div className="recent-list">{children}</div>
      )}
    </div>
  );
}

function MessageModal({ application, onClose }: { application: Application; onClose: () => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="card message-modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ margin: "0 0 4px", fontSize: "1.3rem" }}>Messages</h2>
            <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--ink-500)" }}>
              Application {application.application_id.slice(0, 8)}
            </p>
          </div>
          <button className="btn ghost" type="button" onClick={onClose}>
            Close
          </button>
        </div>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <MessageThread
            shiftId={application.shift_id}
            applicationId={application.application_id}
            currentUserRole="operator"
          />
        </div>
      </div>
    </div>
  );
}

async function loadShifts(applications: Application[]) {
  const shiftIds = unique(applications.map((item) => item.shift_id));
  const shifts = await Promise.all(shiftIds.map((id) => fetchJson<ShiftSummary>(`/shifts/${id}`)));
  return Object.fromEntries(shifts.map((shift) => [shift.shift_id, shift]));
}

async function loadWorkers(applications: Application[]) {
  const workerIds = unique(applications.map((item) => item.worker_id));
  const workers = await Promise.all(workerIds.map((id) => fetchJson<WorkerProfile>(`/workers/${id}`)));
  return Object.fromEntries(workers.map((worker) => [worker.worker_id, worker]));
}

function unique(values: string[]) {
  return Array.from(new Set(values));
}

function bySoonestStart(left: Application, right: Application) {
  return new Date(left.start_time).getTime() - new Date(right.start_time).getTime();
}

function byNewestDecision(left: Application, right: Application) {
  return new Date(right.decided_at ?? right.created_at).getTime()
    - new Date(left.decided_at ?? left.created_at).getTime();
}
