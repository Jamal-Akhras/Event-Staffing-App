import { Link } from "react-router-dom";

import { clock, type TonightRow } from "./dashboardUtils";

export function TonightCard({ rows }: { rows: TonightRow[] }) {
  if (!rows.length) {
    return (
      <section className="ov-card">
        <div className="ov-card-head">
          <span className="ov-kicker ocean">Tonight</span>
        </div>
        <h2 className="ov-card-title">No shifts tonight</h2>
        <p className="ov-muted">Post a shift and it goes live to workers in your market straight away.</p>
        <Link to="/app/shifts" className="ov-btn ov-btn-primary ov-inline-btn">Post a shift</Link>
      </section>
    );
  }

  const first = rows[0].shift;
  const last = rows[rows.length - 1].shift;
  const locations = Array.from(new Set(rows.map((row) => row.shift.location)));

  return (
    <section className="ov-card">
      <div className="ov-card-head">
        <span className="ov-kicker ocean">Tonight · {rows.length === 1 ? first.role : `${rows.length} shifts`}</span>
        <span className="ov-card-time">{clock(first.start_time)} – {clock(last.end_time)}</span>
      </div>
      <h2 className="ov-card-title">{locations.join(" & ")}</h2>
      <div className="ov-rows">
        {rows.map(({ shift, names, codes, missing }) => (
          <div key={shift.shift_id} className="ov-row">
            <span className="ov-row-role">{shift.role} × {shift.workers_needed}</span>
            <span className="ov-row-names">
              {names.length ? names.map((name, index) => (codes[index] ? `${name} · code ${codes[index]}` : name)).join(", ") : "Nobody booked yet"}
            </span>
            {missing === 0 ? (
              <span className="ov-status ok">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M5 13l4 4L19 7" />
                </svg>
                Confirmed
              </span>
            ) : (
              <Link to="/app/applications" className="ov-status warn">{missing} open · Find cover</Link>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
