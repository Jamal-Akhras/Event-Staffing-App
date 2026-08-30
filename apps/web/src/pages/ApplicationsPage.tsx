import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { CancellationModal } from "../components/CancellationModal";
import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { MessageThread } from "../components/MessageThread";
import { PageHeader } from "../components/PageHeader";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { WorkerRail } from "../components/WorkerRail";
import { track } from "../lib/analytics";
import { fetchJson, postJson } from "../lib/api";
import type { Application, CompletedShift } from "../types/operations";
import { DecidedList } from "./applications/DecidedList";
import { RateList } from "./applications/RateList";
import { ShiftGroup } from "./applications/ShiftGroup";
import { buildGroups, lastWorkedLabel, workerHistory, type Applicant } from "./applications/applicationsUtils";
import { completedCounts } from "./dashboard/dashboardUtils";
import { useDecideApplication } from "./dashboard/useOverviewData";
import { useOperationsData } from "./applications/useApplicationsData";
import "../components/Modal.css";
import "./ApplicationsPage.css";

type TabKey = "needs" | "booked" | "declined" | "rate";

export function ApplicationsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const now = new Date();
  const data = useOperationsData(now);
  const completed = useQuery({
    queryKey: ["completed-shifts"],
    queryFn: () => fetchJson<CompletedShift[]>("/accounts/me/completed-shifts"),
  });
  const decide = useDecideApplication(
    (message) => toast({ type: "success", message }),
    (message) => toast({ type: "error", message })
  );
  const [tab, setTab] = useState<TabKey>("needs");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messaging, setMessaging] = useState<Application | null>(null);
  const [cancelling, setCancelling] = useState<Application | null>(null);

  if (data.error) return <ErrorCard message={data.error.message} />;
  if (data.loading) {
    return (
      <div className="pg">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={6} />
      </div>
    );
  }

  const worked = completedCounts(data.activity);
  const pending = data.applications.filter((application) => application.status === "applied");
  const booked = data.applications.filter((application) => application.status === "approved");
  const declined = data.applications.filter(
    (application) => application.status === "rejected" || application.status === "withdrawn"
  );
  const unrated = (completed.data ?? []).filter((shift) => shift.operator_rating === null);
  const groups = buildGroups(pending, data.shifts, data.workers, worked, now);
  const bookingsById = Object.fromEntries(data.bookings.map((booking) => [booking.booking_id, booking]));

  const applicants = groups.flatMap((group) => group.applicants);
  const selected =
    applicants.find((applicant) => applicant.application.application_id === selectedId) ?? applicants[0];
  const openSeats = groups.reduce((sum, group) => sum + group.openSeats, 0);

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: "needs", label: "Needs decision", count: pending.length },
    { key: "booked", label: "Booked", count: booked.length },
    { key: "declined", label: "Declined", count: declined.length },
    { key: "rate", label: "Waiting on a rating", count: unrated.length },
  ];

  const refresh = () =>
    Promise.all(
      ["applications", "shifts", "bookings", "completed-shifts"].map((key) =>
        queryClient.invalidateQueries({ queryKey: [key] })
      )
    );

  return (
    <div className="pg">
      <PageHeader
        title="Applications"
        lead={
          pending.length === 0
            ? "Nobody is waiting on you."
            : `${pending.length} ${pending.length === 1 ? "person is" : "people are"} waiting on you.`
        }
        emphasis={openSeats > 0 ? `${openSeats} ${openSeats === 1 ? "seat" : "seats"} still open.` : undefined}
      />

      <div className="pg-tabs" role="tablist">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={tab === item.key}
            className={tab === item.key ? "on" : ""}
            onClick={() => setTab(item.key)}
          >
            {item.label}
            {item.count > 0 && <small>{item.count}</small>}
          </button>
        ))}
      </div>

      <div className="ap-layout">
        <div className="ap-queue">
          {tab === "needs" &&
            (groups.length === 0 ? (
              <EmptyState
                title="No applications waiting"
                message="New applications land here grouped by the shift they were sent for."
              />
            ) : (
              groups.map((group) => (
                <ShiftGroup
                  key={group.shift.shift_id}
                  group={group}
                  now={now}
                  selectedId={selected?.application.application_id ?? null}
                  busyId={decide.isPending ? decide.variables?.applicationId ?? null : null}
                  onSelect={(applicant: Applicant) => {
                    track("applicant.viewed", {
                      subject_type: "application",
                      subject_id: applicant.application.application_id,
                      context: { worked_here: applicant.workedHere, shift_id: applicant.application.shift_id },
                    });
                    setSelectedId(applicant.application.application_id);
                  }}
                  onDecide={(applicationId, action) => decide.mutate({ applicationId, action })}
                />
              ))
            ))}

          {tab === "booked" && (
            <DecidedList
              applications={booked}
              shifts={data.shifts}
              workers={data.workers}
              bookings={bookingsById}
              emptyTitle="Nobody booked yet"
              emptyMessage="Workers you approve appear here with the state of their shift."
              onMessage={setMessaging}
              onCancel={setCancelling}
            />
          )}

          {tab === "declined" && (
            <DecidedList
              applications={declined}
              shifts={data.shifts}
              workers={data.workers}
              bookings={bookingsById}
              emptyTitle="Nothing declined"
              emptyMessage="Applications you decline, and those workers withdraw, are kept here as a record."
              onMessage={setMessaging}
            />
          )}

          {tab === "rate" && <RateList shifts={unrated} workers={data.workers} onRated={refresh} />}
        </div>

        {selected?.worker && (
          <WorkerRail
            worker={selected.worker}
            kicker="Applicant"
            stats={[
              { label: "With you", value: `${selected.workedHere} shifts` },
              { label: "Last worked", value: lastWorkedLabel(data.bookings, selected.worker.worker_id) },
            ]}
            historyTitle="Shifts with you"
            history={workerHistory(data.bookings, data.shifts, selected.worker.worker_id)}
            note={{
              kicker: "Why this order",
              title: "Regulars first, then reliability",
              body: "People who have worked here before sit at the top of each shift. Everyone else is ordered by how often they turn up.",
            }}
            actions={
              <>
                <button
                  type="button"
                  className="btn primary"
                  disabled={decide.isPending}
                  onClick={() =>
                    decide.mutate({ applicationId: selected.application.application_id, action: "approve" })
                  }
                >
                  Approve
                </button>
                <button type="button" className="btn ghost" onClick={() => setMessaging(selected.application)}>
                  Message
                </button>
              </>
            }
          />
        )}
      </div>

      {messaging && (
        <div className="modal-backdrop" onClick={() => setMessaging(null)}>
          <section className="card modal ap-message" onClick={(event) => event.stopPropagation()}>
            <header className="modal-header">
              <div>
                <h2>{data.workers[messaging.worker_id]?.display_name ?? "Worker"}</h2>
                <p className="ap-status">Messages about this shift</p>
              </div>
              <button type="button" className="btn ghost" onClick={() => setMessaging(null)}>
                Close
              </button>
            </header>
            <MessageThread
              shiftId={messaging.shift_id}
              applicationId={messaging.application_id}
              currentUserRole="operator"
            />
          </section>
        </div>
      )}

      {cancelling?.booking_id && (
        <CancellationModal
          title={`Cancel ${data.workers[cancelling.worker_id]?.display_name ?? "this worker"}'s booking?`}
          consequence="The worker is removed from the shift, the seat reopens, and they receive your reason."
          confirmLabel="Cancel booking"
          onClose={() => setCancelling(null)}
          onConfirm={async (reason) => {
            await postJson(`/bookings/${cancelling.booking_id}/cancel/operator`, {
              reason,
              now: new Date().toISOString(),
            });
            setCancelling(null);
            await refresh();
            toast({ type: "success", message: "Booking cancelled and the worker notified." });
          }}
        />
      )}
    </div>
  );
}
