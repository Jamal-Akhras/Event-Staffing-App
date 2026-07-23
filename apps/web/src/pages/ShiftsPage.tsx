import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { ShiftCreateForm } from "../components/ShiftCreateForm";
import { SkeletonCard } from "../components/SkeletonCard";
import { StatusBadge } from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { formatMoney } from "../lib/format";

type Shift = {
  shift_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  notes?: string | null;
  status: string;
  workers_needed: number;
  workers_filled: number;
  currency?: string;
};

import { API_BASE, getAuthHeaders } from "../lib/api";
import "./ShiftsPage.css";

const resolvedApiBase = API_BASE;

export function ShiftsPage() {
  const { toast } = useToast();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadShifts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${resolvedApiBase}/shifts`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      setShifts(await response.json());
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
          onError={(message) => {
            if (message) toast({ type: "error", message });
          }}
        />
        <ShiftColumn title="Open Shifts" shifts={openShifts} emptyStatus="open" />
        {filledShifts.length > 0 && (
          <ShiftColumn title="Filled Shifts" shifts={filledShifts} emptyStatus="filled" />
        )}
      </div>}
    </div>
  );
}

function ShiftColumn({
  title,
  shifts,
  emptyStatus,
}: {
  title: string;
  shifts: Shift[];
  emptyStatus: "open" | "filled";
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
            <ShiftCard key={shift.shift_id} shift={shift} />
          ))}
        </div>
      )}
    </div>
  );
}

function ShiftCard({ shift }: { shift: Shift }) {
  const remaining = Math.max(shift.workers_needed - shift.workers_filled, 0);

  return (
    <div className={`application-card shift-card ${shift.status}`}>
      <div>
        <div className="shift-card-header">
          <p className="booking-id">
            {shift.shift_id}
          </p>
          <StatusBadge status={shift.status} variant="shift" />
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
      </div>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
