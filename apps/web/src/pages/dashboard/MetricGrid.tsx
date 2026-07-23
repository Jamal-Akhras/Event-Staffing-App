import { Icon } from "../../components/Icon";
import type { DashboardMetric } from "./dashboardUtils";

type MetricGridProps = {
  metrics: DashboardMetric[];
  loading: boolean;
};

export function MetricGrid({ metrics, loading }: MetricGridProps) {
  return (
    <div className="dashboard-grid">
      {metrics.map((metric) => (
        <div key={metric.label} className={`metric-card card ${metric.tone ?? ""}`}>
          <div className="metric-header">
            <span className="metric-icon">
              <Icon name={metric.icon} size={18} />
            </span>
            <h3 className="metric-label">{metric.label}</h3>
          </div>
          <p className="metric-value">{loading ? "..." : metric.value}</p>
          <p className="metric-change">
            {metric.tone === "warning" && <Icon name="alert-triangle" size={14} />}
            {metric.tone === "success" && <Icon name="check" size={14} />}
            {metric.note}
          </p>
        </div>
      ))}
    </div>
  );
}
