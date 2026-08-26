import { Link } from "react-router-dom";

import { greetingFor } from "./dashboardUtils";

type OverviewHeaderProps = {
  venueName: string;
  now: Date;
  lead: string;
  emphasis: string;
};

export function OverviewHeader({ venueName, now, lead, emphasis }: OverviewHeaderProps) {
  return (
    <div className="ov-header">
      <div className="ov-header-copy">
        <p className="ov-eyebrow">
          <span className="ov-eyebrow-dot" aria-hidden="true" />
          {now.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}
        </p>
        <h1 className="ov-title">{greetingFor(now)}, {venueName}.</h1>
        <p className="ov-lead">
          {lead} <em>{emphasis}</em>
        </p>
      </div>
      <div className="ov-header-actions">
        <Link to="/app/templates" className="ov-btn ov-btn-light">Use a template</Link>
        <Link to="/app/shifts" className="ov-btn ov-btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Post a shift
        </Link>
      </div>
    </div>
  );
}
