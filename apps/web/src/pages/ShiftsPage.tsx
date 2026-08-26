import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { ShiftCreateForm } from "../components/ShiftCreateForm";
import { SkeletonCard } from "../components/SkeletonCard";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { formatDateTime, formatMoney } from "../lib/format";
import { fetchJson } from "../lib/api";
import type { Shift } from "../types/operations";
import { ShiftManagementModal } from "./shifts/ShiftManagementModal";
import "./ShiftsPage.css";

export function ShiftsPage() {
  const { toast } = useToast();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedShift, setSelectedShift] = useState<Shift | null>(null);

  const loadShifts = async () => {
    setLoading(true);
    try {
      setShifts(await fetchJson<Shift[]>("/shifts"));
      setLoadError(null);
    } catch (err) {
      toast({ type: "error", message: (err as Error).message });
      setShifts([]);
      setLoadError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShifts();
  }, []);

  const openShifts = useMemo(
    () => shifts.filter((shift) => shift.status === "open"),
    [shifts]
  );
  const filledShifts = useMemo(
    () => shifts.filter((shift) => shift.status === "filled"),
    [shifts]
  );
  const inactiveShifts = useMemo(
    () => shifts.filter((shift) => shift.status === "closed" || shift.status === "cancelled"),
    [shifts]
  );
  const initialLoading = loading && shifts.length === 0 && !loadError;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Shifts</h1>
          <p className="page-subtitle">Post coverage needs and monitor fill status</p>
        </div>
        <button className="btn secondary" type="button" onClick={loadShifts}>
          Refresh
        </button>
      </div>

      {initialLoading && (
        <div className="workspace">
          <SkeletonCard className="shifts-skeleton-form" lines={6} />
          <SkeletonCard className="shifts-skeleton-list" lines={5} />
          <SkeletonCard className="shifts-skeleton-list" lines={5} />
        </div>
      )}
      {!initialLoading && loadError && <ErrorCard message={loadError} />}

      {!initialLoading && !loadError && <div className="workspace">
        <ShiftCreateForm
          onCreated={loadShifts}
          onError={(message) => toast({ type: "error", message })}
        />
        <ShiftColumn title="Open Shifts" shifts={openShifts} emptyStatus="open" onManage={setSelectedShift} />
        {filledShifts.length > 0 && (
          <ShiftColumn title="Filled Shifts" shifts={filledShifts} emptyStatus="filled" onManage={setSelectedShift} />
        )}
        {inactiveShifts.length > 0 && (
          <ShiftColumn title="Closed & Cancelled" shifts={inactiveShifts} emptyStatus="inactive" onManage={setSelectedShift} />
        )}
      </div>}

      {selectedShift && (
        <ShiftManagementModal
          shift={selectedShift}
          onClose={() => setSelectedShift(null)}
          onSaved={async (message) => {
            setSelectedShift(null);
            await loadShifts();
            toast({ type: "success", message });
          }}
        />
      )}
    </div>
  );
}

function ShiftColumn({
  title,
  shifts,
  emptyStatus,
  onManage,
}: {
  title: string;
  shifts: Shift[];
  emptyStatus: "open" | "filled" | "inactive";
  onManage: (shift: Shift) => void;
}) {
  return (
    <div className="panel card">
      <div className="panel-title">
        <h3>{title}</h3>
        <span className="pill">{shifts.length} {emptyStatus}</span>
      </div>
      {shifts.length === 0 ? (
        <EmptyState
          title={`No ${emptyStatus} shifts`}
          message="Post a shift to start receiving applications from qualified workers."
        />
      ) : (
        <div className="recent-list">
          {shifts.map((shift) => (
            <ShiftCard key={shift.shift_id} shift={shift} onManage={() => onManage(shift)} />
          ))}
        </div>
      )}
    </div>
  );
}

function ShiftCard({ shift, onManage }: { shift: Shift; onManage: () => void }) {
  const remaining = Math.max(shift.workers_needed - shift.workers_filled, 0);

  return (
    <div className={`application-card shift-card ${shift.status}`}>
      <div>
        <div className="shift-card-header">
          <p className="booking-id">
            {shift.shift_id}
          </p>
          <StatusBadge status={shift.status} />
        </div>
        <p className="booking-state">{shift.role}</p>
        <p className="booking-meta">{shift.location}</p>
        <p className="booking-meta">{formatDateTime(shift.start_time)}</p>
        <p className="booking-meta">{formatMoney(shift.pay_rate, shift.currency)}/hr</p>
        <p className="booking-meta">
          {shift.workers_filled} of {shift.workers_needed} workers filled
          {remaining > 0 ? ` - ${remaining} still needed` : ""}
        </p>
        {shift.notes && (
          <p className="booking-meta shift-note">
            {shift.notes}
          </p>
        )}
        {shift.cancellation_reason && (
          <p className="booking-meta shift-cancellation-reason">Reason: {shift.cancellation_reason}</p>
        )}
        <button className="btn ghost compact shift-manage-button" type="button" onClick={onManage}>
          {shift.status === "open" || shift.status === "filled" ? "Manage shift" : "View record"}
        </button>
      </div>
    </div>
  );
}
