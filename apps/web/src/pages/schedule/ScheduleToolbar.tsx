type ScheduleToolbarProps = {
  weekLabel: string;
  onPreviousWeek: () => void;
  onToday: () => void;
  onNextWeek: () => void;
};

export function ScheduleToolbar({
  weekLabel,
  onPreviousWeek,
  onToday,
  onNextWeek,
}: ScheduleToolbarProps) {
  return (
    <div className="schedule-toolbar">
      <h2>{weekLabel}</h2>
      <div className="schedule-toolbar-actions">
        <button className="btn ghost" type="button" onClick={onPreviousWeek}>
          Previous
        </button>
        <button className="btn secondary" type="button" onClick={onToday}>
          Today
        </button>
        <button className="btn ghost" type="button" onClick={onNextWeek}>
          Next
        </button>
      </div>
    </div>
  );
}
