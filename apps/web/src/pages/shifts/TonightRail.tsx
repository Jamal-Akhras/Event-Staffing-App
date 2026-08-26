import type { TonightRow } from "../dashboard/dashboardUtils";

export function TonightRail({ rows }: { rows: TonightRow[] }) {
  const names = rows.flatMap((row) => row.names);
  const missing = rows.reduce((sum, row) => sum + row.missing, 0);
  const title = rows.length === 0 ? "Nothing on tonight" : `${names.length} confirmed`;
  const text = rows.length === 0
    ? "Post a shift and it goes live to workers straight away."
    : `${joinNames(names)}${missing > 0 ? ` Still ${missing} open.` : " Everyone is booked."}`;

  return (
    <section className="bd-tonight">
      <span className="bd-tonight-kicker">Tonight</span>
      <span className="bd-tonight-title">{title}</span>
      <span className="bd-tonight-text">{text}</span>
    </section>
  );
}

function joinNames(names: string[]) {
  if (names.length === 0) return "Nobody booked yet.";
  if (names.length === 1) return `${names[0]}.`;
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}.`;
}
