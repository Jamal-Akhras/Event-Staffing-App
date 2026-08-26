import { Link } from "react-router-dom";

import { initials } from "../../lib/useVenue";
import type { Regular } from "./dashboardUtils";

const PALETTE = ["#f5a524", "#eee4d7", "#fffaf2"];

export function RegularsCard({ regulars }: { regulars: Regular[] }) {
  const shown = regulars.slice(0, 3);
  const extra = regulars.length - shown.length;
  return (
    <section className="ov-regulars">
      <div className="ov-avatars" aria-hidden="true">
        {shown.map((entry, index) => (
          <span
            key={entry.worker.worker_id}
            className="ov-avatar-stack"
            style={{ background: PALETTE[index], color: "var(--ink-900)" }}
          >
            {initials(entry.worker.display_name || "W")}
          </span>
        ))}
        {extra > 0 && <span className="ov-avatar-stack more">+{extra}</span>}
        {shown.length === 0 && <span className="ov-avatar-stack more">0</span>}
      </div>
      <div className="ov-regulars-copy">
        <span className="ov-regulars-title">Your regulars</span>
        <span className="ov-regulars-text">
          {regulars.length > 0
            ? `${regulars.length} ${regulars.length === 1 ? "person has" : "people have"} worked with you three times or more.`
            : "Workers who complete three shifts with you will appear here."}
        </span>
      </div>
      <Link to="/app/workers" className="ov-regulars-link">Workers</Link>
    </section>
  );
}
