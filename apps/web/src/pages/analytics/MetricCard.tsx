type MetricCardProps = {
  label: string;
  value: string;
  note: string;
  trend: number[];
};

export function MetricCard({ label, value, note, trend }: MetricCardProps) {
  const peak = Math.max(...trend, 1);
  return (
    <div className="an-metric">
      <span className="an-metric-label">{label}</span>
      <p className="an-metric-value">{value}</p>
      <span className="an-metric-note">{note}</span>
      <Sparkline values={trend} peak={peak} />
    </div>
  );
}

function Sparkline({ values, peak }: { values: number[]; peak: number }) {
  if (values.length === 0) return null;
  return (
    <div className="an-spark" aria-hidden="true">
      {values.map((value, index) => (
        <i
          key={index}
          className={index === values.length - 1 ? "on" : ""}
          style={{ height: `${Math.max((value / peak) * 100, 4)}%` }}
        />
      ))}
    </div>
  );
}
