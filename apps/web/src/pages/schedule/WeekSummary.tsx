type WeekSummaryProps = {
  total: number;
  open: number;
  filled: number;
  seatsOpen: number;
};

export function WeekSummary({ total, open, filled, seatsOpen }: WeekSummaryProps) {
  return (
    <div className="card schedule-summary">
      <h3>This Week Summary</h3>
      <div className="schedule-summary-grid">
        <Metric label="Total Shifts" value={total} />
        <Metric label="Open Shifts" value={open} tone="warning" />
        <Metric label="Filled Shifts" value={filled} tone="success" />
        <Metric label="Open Seats" value={seatsOpen} tone="info" />
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "warning" | "success" | "info";
}) {
  return (
    <div className={`application-card schedule-summary-metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
