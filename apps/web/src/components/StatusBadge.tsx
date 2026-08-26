import type { CSSProperties } from "react";

import "./StatusBadge.css";

type StatusBadgeProps = {
  status: string;
};

type StatusConfig = {
  color: string;
  bgColor: string;
  label: string;
};

const STATUS_CONFIGS: Record<string, StatusConfig> = {
  open: statusConfig("#10B981", "rgba(16, 185, 129, 0.1)", "OPEN"),
  filled: statusConfig("#10B981", "rgba(16, 185, 129, 0.1)", "FILLED"),
  partial: statusConfig("#F59E0B", "rgba(245, 158, 11, 0.1)", "PARTIAL"),
  created: statusConfig("#3B82F6", "rgba(59, 130, 246, 0.1)", "CREATED"),
  confirmed: statusConfig("#3B82F6", "rgba(59, 130, 246, 0.1)", "CONFIRMED"),
  checked_in: statusConfig("#3B82F6", "rgba(59, 130, 246, 0.1)", "CHECKED IN"),
  checked_out: statusConfig("#3B82F6", "rgba(59, 130, 246, 0.1)", "CHECKED OUT"),
  approved: statusConfig("#10B981", "rgba(16, 185, 129, 0.1)", "APPROVED"),
  paid: statusConfig("#10B981", "rgba(16, 185, 129, 0.1)", "PAID"),
  cancelled_by_worker: statusConfig("#EF4444", "rgba(239, 68, 68, 0.1)", "CANCELLED"),
  cancelled_by_operator: statusConfig("#EF4444", "rgba(239, 68, 68, 0.1)", "CANCELLED"),
  no_show: statusConfig("#EF4444", "rgba(239, 68, 68, 0.1)", "NO SHOW"),
  applied: statusConfig("#F59E0B", "rgba(245, 158, 11, 0.1)", "APPLIED"),
  rejected: statusConfig("#EF4444", "rgba(239, 68, 68, 0.1)", "REJECTED"),
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config =
    STATUS_CONFIGS[status] ??
    statusConfig("#6B7785", "rgba(107, 119, 133, 0.1)", status.toUpperCase());

  return (
    <span
      className="status-badge"
      style={{
        "--status-color": config.color,
        "--status-bg": config.bgColor,
      } as CSSProperties}
    >
      <span className="status-badge-dot" aria-hidden="true" />
      {config.label}
    </span>
  );
}

function statusConfig(color: string, bgColor: string, label: string): StatusConfig {
  return { color, bgColor, label };
}
