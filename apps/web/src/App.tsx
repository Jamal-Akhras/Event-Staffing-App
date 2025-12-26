import { FormEvent, useEffect, useMemo, useState } from "react";

type HealthStatus = {
  status: string;
};

type Booking = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  state: string;
  allowed_transitions: string[];
  created_at?: string | null;
  confirmed_at?: string | null;
  checked_in_at?: string | null;
  checked_out_at?: string | null;
  approved_at?: string | null;
  paid_at?: string | null;
  cancelled_at?: string | null;
  no_show_at?: string | null;
};

type Shift = {
  shift_id: string;
  operator_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  notes?: string | null;
  status: string;
  created_at: string;
};

type Application = {
  application_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
};

type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  updated_at: string;
};

const apiBase = import.meta.env.VITE_API_BASE ?? "";
const resolvedApiBase =
  apiBase || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");
const operatorHeaders = {
  "X-Actor-Role": "operator",
  "Content-Type": "application/json",
};

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<Booking | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [recentBookings, setRecentBookings] = useState<Booking[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationsError, setApplicationsError] = useState<string | null>(null);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [shiftError, setShiftError] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<WorkerProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({
    shift_id: "shift-1",
    worker_id: "worker-1",
    operator_id: "operator-1",
    start_time: "",
    end_time: "",
  });
  const [shiftForm, setShiftForm] = useState({
    operator_id: "operator-1",
    role: "server",
    location: "Downtown",
    start_time: "",
    end_time: "",
    pay_rate: "25",
    notes: "",
  });
  const [lookupId, setLookupId] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${resolvedApiBase}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setHealth(data))
      .catch((err) => {
        if ((err as Error).name === "AbortError") {
          return;
        }
        setError((err as Error).message);
      });

    return () => controller.abort();
  }, []);

  const loadRecent = async () => {
    try {
      const response = await fetch(`${resolvedApiBase}/bookings`, {
        headers: operatorHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking[];
      setRecentBookings(data);
    } catch {
      setRecentBookings([]);
    }
  };

  const loadApplications = async () => {
    try {
      const response = await fetch(`${resolvedApiBase}/applications`, {
        headers: operatorHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Application[];
      setApplications(data);
      setApplicationsError(null);
    } catch (err) {
      setApplications([]);
      setApplicationsError((err as Error).message);
    }
  };

  const loadShifts = async () => {
    try {
      const response = await fetch(`${resolvedApiBase}/shifts`, {
        headers: operatorHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Shift[];
      setShifts(data);
      setShiftError(null);
    } catch (err) {
      setShifts([]);
      setShiftError((err as Error).message);
    }
  };

  const loadWorkerProfile = async (workerId: string) => {
    setProfileError(null);
    try {
      const response = await fetch(`${resolvedApiBase}/workers/${workerId}`, {
        headers: operatorHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as WorkerProfile;
      setSelectedProfile(data);
    } catch (err) {
      setProfileError((err as Error).message);
      setSelectedProfile(null);
    }
  };

  useEffect(() => {
    loadRecent();
    loadApplications();
    loadShifts();
  }, []);

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault();
    setBookingError(null);

    try {
      const payload = {
        ...formValues,
        start_time: new Date(formValues.start_time).toISOString(),
        end_time: new Date(formValues.end_time).toISOString(),
        now: new Date().toISOString(),
      };
      const response = await fetch(`${resolvedApiBase}/bookings`, {
        method: "POST",
        headers: operatorHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking;
      setBooking(data);
      setLookupId(data.booking_id);
      await loadRecent();
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const handleCreateShift = async (event: FormEvent) => {
    event.preventDefault();
    setShiftError(null);

    try {
      const payload = {
        ...shiftForm,
        pay_rate: Number(shiftForm.pay_rate),
        start_time: new Date(shiftForm.start_time).toISOString(),
        end_time: new Date(shiftForm.end_time).toISOString(),
        notes: shiftForm.notes || null,
        now: new Date().toISOString(),
      };
      const response = await fetch(`${resolvedApiBase}/shifts`, {
        method: "POST",
        headers: operatorHeaders,
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      await loadShifts();
    } catch (err) {
      setShiftError((err as Error).message);
    }
  };

  const handleLookup = async () => {
    if (!lookupId.trim()) {
      return;
    }
    setBookingError(null);
    try {
      const response = await fetch(`${resolvedApiBase}/bookings/${lookupId}`, {
        headers: operatorHeaders,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking;
      setBooking(data);
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const transition = async (path: string) => {
    if (!booking) {
      return;
    }
    setBookingError(null);
    try {
      const response = await fetch(`${resolvedApiBase}${path}`, {
        method: "POST",
        headers: operatorHeaders,
        body: JSON.stringify({ now: new Date().toISOString() }),
      });
      if (!response.ok) {
        const errorPayload = await response.json();
        throw new Error(errorPayload?.detail ?? `API error: ${response.status}`);
      }
      const data = (await response.json()) as Booking;
      setBooking(data);
      await loadRecent();
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const decideApplication = async (applicationId: string, action: "approve" | "reject") => {
    setApplicationsError(null);
    try {
      const response = await fetch(`${resolvedApiBase}/applications/${applicationId}/${action}`, {
        method: "POST",
        headers: operatorHeaders,
        body: JSON.stringify({ now: new Date().toISOString() }),
      });
      if (!response.ok) {
        const errorPayload = await response.json();
        throw new Error(errorPayload?.detail ?? `API error: ${response.status}`);
      }
      await loadApplications();
      await loadRecent();
      await loadShifts();
    } catch (err) {
      setApplicationsError((err as Error).message);
    }
  };

  const operatorAllowed = new Set([
    "confirmed",
    "approved",
    "paid",
    "no_show",
    "cancelled_by_operator",
  ]);
  const canTransition = (state: string) =>
    operatorAllowed.has(state) &&
    (booking?.allowed_transitions?.includes(state) ?? false);

  const openShifts = useMemo(() => shifts.filter((shift) => shift.status === "open"), [shifts]);

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" />
          <div>
            <p className="brand-eyebrow">Reliability-first ops</p>
            <p className="brand-title">Event Staffing</p>
          </div>
        </div>
        <div className="status-pill">
          <span className="status-label">API</span>
          {error && <span className="status error">{error}</span>}
          {!error && !health && <span className="status pending">Checking</span>}
          {health && <span className="status ok">Healthy</span>}
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Control room</p>
          <h1>Command staffing with the polish of a premium marketplace.</h1>
          <p className="subtitle">
            Manage shifts, applications, and booking lifecycles with the speed and
            clarity operators expect.
          </p>
          <div className="hero-actions">
            <button className="btn primary" type="button" onClick={loadShifts}>
              Refresh shifts
            </button>
            <button className="btn ghost" type="button" onClick={loadApplications}>
              View applications
            </button>
          </div>
        </div>
        <div className="hero-card">
          <div className="hero-card-header">
            <h2>Live API</h2>
            <span className="pill">GET /health</span>
          </div>
          <div className="hero-card-body">
            {error && <p className="status error">{error}</p>}
            {!error && !health && <p className="status pending">Checking...</p>}
            {health && <p className="status ok">Healthy</p>}
            <p className="status-meta">
              Runtime status updates for operator consoles and worker apps.
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <h2>Operations</h2>
            <p>Post shifts, confirm bookings, and manage outcomes from one place.</p>
          </div>
          <button className="btn secondary" type="button" onClick={loadRecent}>
            Refresh bookings
          </button>
        </div>
        <div className="workspace">
          <div className="panel card">
            <div className="panel-title">
              <h3>Create Shift</h3>
              <span className="pill">Operator</span>
            </div>
          <form className="form" onSubmit={handleCreateShift}>
            <label>
              Operator ID
              <input
                value={shiftForm.operator_id}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, operator_id: event.target.value })
                }
              />
            </label>
            <label>
              Role
              <input
                value={shiftForm.role}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, role: event.target.value })
                }
              />
            </label>
            <label>
              Location
              <input
                value={shiftForm.location}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, location: event.target.value })
                }
              />
            </label>
            <label>
              Start time
              <input
                type="datetime-local"
                value={shiftForm.start_time}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, start_time: event.target.value })
                }
                required
              />
            </label>
            <label>
              End time
              <input
                type="datetime-local"
                value={shiftForm.end_time}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, end_time: event.target.value })
                }
                required
              />
            </label>
            <label>
              Pay rate
              <input
                value={shiftForm.pay_rate}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, pay_rate: event.target.value })
                }
              />
            </label>
            <label>
              Notes
              <input
                value={shiftForm.notes}
                onChange={(event) =>
                  setShiftForm({ ...shiftForm, notes: event.target.value })
                }
              />
            </label>
            <button className="btn primary" type="submit">
              Post shift
            </button>
            {shiftError && <p className="status error">{shiftError}</p>}
          </form>
          </div>
          <div className="panel card">
            <div className="panel-title">
              <h3>Open Shifts</h3>
              <span className="pill">Live</span>
            </div>
          {openShifts.length === 0 && (
            <p className="status pending">No open shifts.</p>
          )}
          <div className="recent-list">
            {openShifts.map((shift) => (
              <div key={shift.shift_id} className="application-card">
                <div>
                  <p className="booking-id">{shift.shift_id}</p>
                  <p className="booking-state">{shift.role}</p>
                  <p className="booking-meta">
                    {shift.location} - {shift.start_time}
                  </p>
                  <p className="booking-meta">${shift.pay_rate.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
          </div>
          <div className="panel card">
            <div className="panel-title">
              <h3>Create Booking</h3>
              <span className="pill">Lifecycle</span>
            </div>
          <form className="form" onSubmit={handleCreate}>
            <label>
              Shift ID
              <input
                value={formValues.shift_id}
                onChange={(event) =>
                  setFormValues({ ...formValues, shift_id: event.target.value })
                }
              />
            </label>
            <label>
              Worker ID
              <input
                value={formValues.worker_id}
                onChange={(event) =>
                  setFormValues({ ...formValues, worker_id: event.target.value })
                }
              />
            </label>
            <label>
              Operator ID
              <input
                value={formValues.operator_id}
                onChange={(event) =>
                  setFormValues({ ...formValues, operator_id: event.target.value })
                }
              />
            </label>
            <label>
              Start time
              <input
                type="datetime-local"
                value={formValues.start_time}
                onChange={(event) =>
                  setFormValues({ ...formValues, start_time: event.target.value })
                }
                required
              />
            </label>
            <label>
              End time
              <input
                type="datetime-local"
                value={formValues.end_time}
                onChange={(event) =>
                  setFormValues({ ...formValues, end_time: event.target.value })
                }
                required
              />
            </label>
            <button className="btn primary" type="submit">
              Create booking
            </button>
          </form>
          </div>
          <div className="panel card">
            <div className="panel-title">
              <h3>Booking Status</h3>
              <span className="pill">Operator</span>
            </div>
          <div className="lookup">
            <input
              placeholder="Booking ID"
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
            />
            <button className="btn secondary" type="button" onClick={handleLookup}>
              Load
            </button>
          </div>
          {bookingError && <p className="status error">{bookingError}</p>}
          {!booking && <p className="status pending">No booking loaded.</p>}
          {booking && (
            <div className="booking-card">
              <p className="booking-id">{booking.booking_id}</p>
              <div className="booking-state-row">
                <p className="booking-state">{booking.state}</p>
                <span className="pill">{booking.allowed_transitions.length} actions</span>
              </div>
              <p className="booking-meta">
                {booking.start_time} -&gt; {booking.end_time}
              </p>
              <div className="actions">
                <button
                  className="btn secondary"
                  onClick={() => transition(`/bookings/${booking.booking_id}/confirm`)}
                  disabled={!canTransition("confirmed")}
                >
                  Confirm
                </button>
                <button
                  className="btn secondary"
                  onClick={() => transition(`/bookings/${booking.booking_id}/approve`)}
                  disabled={!canTransition("approved")}
                >
                  Approve
                </button>
                <button
                  className="btn primary"
                  onClick={() => transition(`/bookings/${booking.booking_id}/pay`)}
                  disabled={!canTransition("paid")}
                >
                  Pay
                </button>
                <button
                  className="btn ghost"
                  onClick={() => transition(`/bookings/${booking.booking_id}/no-show`)}
                  disabled={!canTransition("no_show")}
                >
                  No-show
                </button>
                <button
                  className="btn ghost"
                  onClick={() => transition(`/bookings/${booking.booking_id}/cancel/worker`)}
                  disabled
                >
                  Cancel (worker)
                </button>
                <button
                  className="btn ghost"
                  onClick={() => transition(`/bookings/${booking.booking_id}/cancel/operator`)}
                  disabled={!canTransition("cancelled_by_operator")}
                >
                  Cancel (operator)
                </button>
              </div>
            </div>
          )}
          </div>
          <div className="panel card">
            <div className="panel-title">
              <h3>Recent Bookings</h3>
              <span className="pill">Feed</span>
            </div>
          {recentBookings.length === 0 && (
            <p className="status pending">No recent bookings.</p>
          )}
          <div className="recent-list">
            {recentBookings.map((item) => (
              <button
                key={item.booking_id}
                className="recent-item btn ghost"
                onClick={() => {
                  setBooking(item);
                  setLookupId(item.booking_id);
                }}
              >
                <span className="recent-id">{item.booking_id}</span>
                <span className="recent-state">{item.state}</span>
              </button>
            ))}
          </div>
          </div>
          <div className="panel card">
            <div className="panel-title">
              <h3>Applications</h3>
              <span className="pill">Review</span>
            </div>
          {applicationsError && <p className="status error">{applicationsError}</p>}
          {applications.length === 0 && (
            <p className="status pending">No applications yet.</p>
          )}
          <div className="recent-list">
            {applications.map((item) => (
              <div key={item.application_id} className="application-card">
                <div>
                  <p className="booking-id">{item.application_id}</p>
                  <p className="booking-state">{item.status}</p>
                  <p className="booking-meta">
                    Shift {item.shift_id} - Worker {item.worker_id}
                  </p>
                  {item.message && <p className="booking-meta">{item.message}</p>}
                </div>
                <div className="actions">
                  <button
                    className="btn secondary"
                    onClick={() => decideApplication(item.application_id, "approve")}
                    disabled={item.status !== "applied"}
                  >
                    Approve
                  </button>
                  <button
                    className="btn ghost"
                    onClick={() => decideApplication(item.application_id, "reject")}
                    disabled={item.status !== "applied"}
                  >
                    Reject
                  </button>
                  <button
                    className="btn ghost"
                    onClick={() => loadWorkerProfile(item.worker_id)}
                  >
                    View profile
                  </button>
                </div>
              </div>
            ))}
          </div>
          {profileError && <p className="status error">{profileError}</p>}
          {selectedProfile && (
            <div className="profile-panel">
              <div>
                <p className="booking-id">{selectedProfile.worker_id}</p>
                <p className="booking-state">{selectedProfile.display_name}</p>
                <p className="booking-meta">
                  {selectedProfile.role} - {selectedProfile.city}
                </p>
                <p className="booking-meta">
                  Experience: {selectedProfile.experience_years} yrs
                </p>
                <p className="booking-meta">
                  Reliability: {selectedProfile.reliability_score.toFixed(2)}
                </p>
                {selectedProfile.bio && <p className="booking-meta">{selectedProfile.bio}</p>}
                {selectedProfile.languages.length > 0 && (
                  <p className="booking-meta">
                    Languages: {selectedProfile.languages.join(", ")}
                  </p>
                )}
                {selectedProfile.badges.length > 0 && (
                  <p className="booking-meta">
                    Badges: {selectedProfile.badges.join(", ")}
                  </p>
                )}
              </div>
              <div className="actions">
                <button className="btn secondary" onClick={() => setSelectedProfile(null)}>
                  Close
                </button>
              </div>
            </div>
          )}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <h2>Operational Clarity</h2>
            <p>Every step is explicit, auditable, and designed for reliability.</p>
          </div>
        </div>
        <div className="grid">
          <div className="panel card">
            <h3>Operator Flow</h3>
            <ol>
              <li>Post shift</li>
              <li>Review applications</li>
              <li>Approve booking</li>
              <li>Trigger payment</li>
            </ol>
          </div>
          <div className="panel card">
            <h3>Worker Flow</h3>
            <ol>
              <li>Apply for shift</li>
              <li>Check-in window</li>
              <li>Check-out</li>
              <li>Performance recorded</li>
            </ol>
          </div>
          <div className="panel card">
            <h3>System Rules</h3>
            <ol>
              <li>Explicit state machine</li>
              <li>Time-window guards</li>
              <li>Idempotent transitions</li>
              <li>Audit-ready timestamps</li>
            </ol>
          </div>
        </div>
      </section>
    </div>
  );
}
