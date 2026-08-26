type Stat = {
  label: string;
  value: string;
  note: string;
  tone?: "warning" | "success";
};

export function StatRow({ stats }: { stats: Stat[] }) {
  return (
    <div className="ov-stats">
      {stats.map((stat) => (
        <div key={stat.label} className="ov-stat">
          <span className="ov-stat-label">{stat.label}</span>
          <span className="ov-stat-value">{stat.value}</span>
          <span className={`ov-stat-note ${stat.tone ?? ""}`}>{stat.note}</span>
        </div>
      ))}
    </div>
  );
}
