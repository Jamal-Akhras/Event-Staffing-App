import type { DirectoryEntry } from "../workers/directory";
import "./RotaPanels.css";

const EMPLOYED = new Set(["permanent", "part_time", "bank"]);

type ContractedStripProps = {
  entries: DirectoryEntry[];
  scheduled: Map<string, number>;
};

export function ContractedStrip({ entries, scheduled }: ContractedStripProps) {
  const rows = entries.filter(
    (entry) =>
      entry.status === "active" &&
      EMPLOYED.has(entry.relationship_type) &&
      entry.contracted_hours_per_week !== null
  );
  if (rows.length === 0) return null;

  return (
    <section className="rp-contracted">
      <span className="rp-contracted-title">Contracted hours this week</span>
      <div className="rp-contracted-row">
        {rows.map((entry) => {
          const planned = scheduled.get(entry.worker_id) ?? 0;
          const contracted = Number(entry.contracted_hours_per_week);
          const delta = planned - contracted;
          const tone = delta > 0.01 ? "over" : delta < -0.01 ? "under" : "ok";
          const note =
            tone === "ok"
              ? "on contract"
              : tone === "over"
                ? `${trim(delta)}h over`
                : `${trim(-delta)}h under`;
          return (
            <span key={entry.worker_id} className={`rp-contracted-chip ${tone}`}>
              <b>{entry.display_name}</b> {trim(planned)}h of {trim(contracted)}h · {note}
            </span>
          );
        })}
      </div>
    </section>
  );
}

function trim(value: number): string {
  return (Math.round(value * 100) / 100).toString();
}
