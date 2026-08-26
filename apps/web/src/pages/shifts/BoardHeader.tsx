import { WEEKDAYS } from "../../lib/weekStart";
import { boardLabel } from "./boardUtils";

type BoardHeaderProps = {
  days: Date[];
  openSeats: number;
  weekStart: number;
  onWeekStartChange: (day: number) => void;
  onPrevious: () => void;
  onToday: () => void;
  onNext: () => void;
  onPost: () => void;
};

export function BoardHeader({ days, openSeats, weekStart, onWeekStartChange, onPrevious, onToday, onNext, onPost }: BoardHeaderProps) {
  return (
    <div className="bd-header">
      <div className="bd-nav">
        <button type="button" className="bd-nav-arrow" aria-label="Previous week" onClick={onPrevious}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M15 6l-6 6 6 6" />
          </svg>
        </button>
        <button type="button" className="bd-nav-today" onClick={onToday}>Today</button>
        <button type="button" className="bd-nav-arrow" aria-label="Next week" onClick={onNext}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 6l6 6-6 6" />
          </svg>
        </button>
      </div>
      <h1 className="bd-title">{boardLabel(days)}</h1>
      <span className={`bd-seats ${openSeats > 0 ? "" : "ok"}`}>
        {openSeats > 0 ? `${openSeats} open seat${openSeats === 1 ? "" : "s"}` : "All covered"}
      </span>
      <div className="bd-header-actions">
        <label className="bd-week-start">
          Week starts
          <select value={weekStart} onChange={(event) => onWeekStartChange(Number(event.target.value))}>
            {WEEKDAYS.map((name, day) => (
              <option key={name} value={day}>{name.slice(0, 3)}</option>
            ))}
          </select>
        </label>
        <button type="button" className="ov-btn ov-btn-primary bd-post" onClick={onPost}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Post shift
        </button>
      </div>
    </div>
  );
}
