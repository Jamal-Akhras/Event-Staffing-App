import { useEffect, useMemo, useState } from "react";

import { fetchJson } from "../lib/api";
import type { Shift } from "../types/operations";
import { ScheduleGrid } from "./schedule/ScheduleGrid";
import { ScheduleToolbar } from "./schedule/ScheduleToolbar";
import { ShiftDetailsModal } from "./schedule/ShiftDetailsModal";
import { WeekSummary } from "./schedule/WeekSummary";
import {
  getWeekDates,
  getWeekLabel,
  getWeekStart,
  getWeekSummary,
  groupShiftsByDay,
} from "./schedule/scheduleUtils";
import "./SchedulePage.css";

export function SchedulePage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedShift, setSelectedShift] = useState<Shift | null>(null);
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() =>
    getWeekStart(new Date())
  );

  const loadShifts = async () => {
    setLoading(true);
    try {
      setShifts(await fetchJson<Shift[]>("/shifts"));
      setError(null);
    } catch (err) {
      setShifts([]);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShifts();
  }, []);

  const weekDates = useMemo(() => getWeekDates(currentWeekStart), [currentWeekStart]);
  const shiftsByDay = useMemo(
    () => groupShiftsByDay(shifts, weekDates),
    [shifts, weekDates]
  );
  const summary = useMemo(() => getWeekSummary(shiftsByDay), [shiftsByDay]);

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Schedule</h1>
          <p className="page-subtitle">Scan weekly coverage and open seats.</p>
        </div>
        <button className="btn secondary" type="button" onClick={loadShifts}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="card error-card">
          <p className="status error">{error}</p>
        </div>
      )}

      <section className="card schedule-board">
        <ScheduleToolbar
          weekLabel={getWeekLabel(currentWeekStart)}
          onPreviousWeek={() => shiftWeek(-7)}
          onToday={() => setCurrentWeekStart(getWeekStart(new Date()))}
          onNextWeek={() => shiftWeek(7)}
        />

        {loading ? (
          <p className="booking-meta">Loading schedule...</p>
        ) : (
          <ScheduleGrid
            weekDates={weekDates}
            shiftsByDay={shiftsByDay}
            onSelectShift={setSelectedShift}
          />
        )}
      </section>

      <WeekSummary {...summary} />

      {selectedShift && (
        <ShiftDetailsModal
          shift={selectedShift}
          onClose={() => setSelectedShift(null)}
        />
      )}
    </div>
  );

  function shiftWeek(days: number) {
    const nextDate = new Date(currentWeekStart);
    nextDate.setDate(nextDate.getDate() + days);
    setCurrentWeekStart(nextDate);
  }
}
