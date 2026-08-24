import { ReactNode, useEffect, useState } from "react";
import { Application, ApplicationReviewCard, MessageHistory, ShiftSummary, WorkerProfile } from "../components/ApplicationReviewCard";
import { CancellationModal } from "../components/CancellationModal";
import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { MessageThread } from "../components/MessageThread";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { WorkerProfilePanel } from "../components/WorkerProfilePanel";
import type { Booking } from "../types/operations";
import { CompletedShiftsPanel, type CompletedShift } from "./applications/CompletedShiftsPanel";

import { fetchJson, postJson } from "../lib/api";
import "./ApplicationsPage.css";

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
  const [bookingsById, setBookingsById] = useState<Record<string, Booking>>({});
  const [cancellationTarget, setCancellationTarget] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);

  const loadApplications = async () => {
    setLoading(true);
    try {
      const [data, completed, bookings] = await Promise.all([
        fetchJson<Application[]>("/applications"),
        fetchJson<CompletedShift[]>("/accounts/me/completed-shifts").catch(() => [] as CompletedShift[]),
        fetchJson<Booking[]>("/bookings"),
      ]);
      const [shiftMap, workerMap] = await Promise.all([loadShifts(data), loadWorkers(data)]);
      setApplications(data);
      setShiftsById(shiftMap);
      setWorkersById(workerMap);
      setCompletedShifts(completed);
      setBookingsById(Object.fromEntries(bookings.map((booking) => [booking.booking_id, booking])));
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

        <CompletedShiftsPanel
          shifts={completedShifts}
          workersById={workersById}
          onRated={loadApplications}
        />
      </div>}

      {selectedProfile && <WorkerProfilePanel profile={selectedProfile} onClose={() => setSelectedProfile(null)} />}

      {messagingApplication && <MessageModal application={messagingApplication} onClose={() => setMessagingApplication(null)} />}

      {cancellationTarget?.booking_id && (
        <CancellationModal
          title={`Cancel ${workersById[cancellationTarget.worker_id]?.display_name ?? "worker"}'s booking?`}
          consequence="The worker will be removed from this shift, the seat will reopen, and they will receive your reason."
          confirmLabel="Cancel booking"
          onClose={() => setCancellationTarget(null)}
          onConfirm={async (reason) => {
            await postJson(`/bookings/${cancellationTarget.booking_id}/cancel/operator`, {
              reason,
              now: new Date().toISOString(),
            });
            setCancellationTarget(null);
            await loadApplications();
            toast({ type: "success", message: "Booking cancelled and worker notified." });
          }}
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
        bookingState={item.booking_id ? bookingsById[item.booking_id]?.state : undefined}
        onCancelBooking={item.booking_id ? () => setCancellationTarget(item) : undefined}
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
