import type { AnalyticsGap, AnalyticsRole } from "../../types/insights";

function whenLabel(value: string) {
  return new Date(value).toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "short",
  });
}

export function GapList({ gaps }: { gaps: AnalyticsGap[] }) {
  if (gaps.length === 0) {
    return (
      <div className="an-panel">
        <h2 className="an-panel-title">Seats that went unfilled</h2>
        <p className="an-empty">Every seat you posted was covered. Nothing went unfilled this period.</p>
      </div>
    );
  }

  return (
    <div className="an-panel">
      <h2 className="an-panel-title">Seats that went unfilled</h2>
      {gaps.map((gap) => (
        <div key={gap.shift_id} className="an-gap">
          <span className="an-gap-mark" aria-hidden="true" />
          <div className="an-gap-copy">
            <p className="an-gap-title">
              {whenLabel(gap.start_time)} · {gap.role}
            </p>
            <p className="an-gap-reason">{gap.reason}</p>
          </div>
          <span className="an-gap-count">
            {gap.unfilled} {gap.unfilled === 1 ? "seat" : "seats"}
          </span>
        </div>
      ))}
    </div>
  );
}

export function RoleList({ roles }: { roles: AnalyticsRole[] }) {
  return (
    <div className="an-panel">
      <h2 className="an-panel-title">Seats by role</h2>
      {roles.length === 0 ? (
        <p className="an-empty">Nothing posted in this period.</p>
      ) : (
        roles.map((role) => (
          <div key={role.role} className="an-role">
            <span>{role.role}</span>
            <em>{role.seats}</em>
          </div>
        ))
      )}
    </div>
  );
}
