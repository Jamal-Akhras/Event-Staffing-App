import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { PageHeader } from "../components/PageHeader";
import { SkeletonCard } from "../components/SkeletonCard";
import { WorkerRail } from "../components/WorkerRail";
import { fetchJson } from "../lib/api";
import { useRosterActivity } from "../lib/useInsights";
import type { CompletedShift, WorkerProfile } from "../types/operations";
import { StatRow } from "./dashboard/StatRow";
import { RosterTable } from "./workers/RosterTable";
import { RosterRail } from "./workers/RosterRail";
import {
  buildRoster,
  filterRoster,
  rosterStats,
  sortRoster,
  type RosterFilter,
  type RosterSort,
} from "./workers/rosterUtils";
import "./WorkersPage.css";

const FILTERS: { key: RosterFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "regular", label: "Regulars" },
  { key: "new", label: "New" },
  { key: "watch", label: "Watch list" },
];

export function WorkersPage() {
  const workers = useQuery({ queryKey: ["workers-roster"], queryFn: () => fetchJson<WorkerProfile[]>("/workers") });
  const activity = useRosterActivity();
  const completed = useQuery({
    queryKey: ["completed-shifts"],
    queryFn: () => fetchJson<CompletedShift[]>("/accounts/me/completed-shifts"),
  });
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<RosterFilter>("all");
  const [sort, setSort] = useState<RosterSort>("reliability");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const error = [workers, activity, completed].find((item) => item.error)?.error as Error | undefined;
  if (error) return <ErrorCard message={error.message} />;
  if (workers.isPending || activity.isPending || !workers.data || !activity.data) {
    return (
      <div className="pg">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={6} />
      </div>
    );
  }

  const now = new Date();
  const rows = buildRoster(workers.data, activity.data, completed.data ?? []);
  const stats = rosterStats(rows);
  const visible = sortRoster(filterRoster(rows, query, filter), sort);
  const selected = visible.find((row) => row.worker.worker_id === selectedId) ?? visible[0];

  const counts: Record<RosterFilter, number> = {
    all: stats.total,
    regular: stats.regulars,
    new: stats.newcomers,
    watch: stats.watch,
  };

  return (
    <div className="pg">
      <PageHeader
        title="Workers"
        lead={
          stats.total === 0
            ? "Nobody has worked a shift with you yet."
            : `Everyone who has worked a shift with you.`
        }
        emphasis={stats.regulars > 0 ? `${stats.regulars} now count as regulars.` : undefined}
        search={{ value: query, placeholder: "Name, role or city", onChange: setQuery }}
      />

      <div className="wk-summary">
        <StatRow
          stats={[
            { label: "In your roster", value: String(stats.total), note: "People who have applied or worked here" },
            {
              label: "Regulars",
              value: String(stats.regulars),
              note: "Three or more shifts with you",
              tone: stats.regulars > 0 ? "success" : undefined,
            },
            {
              label: "Average reliability",
              value: stats.averageReliability === null ? "—" : `${stats.averageReliability}%`,
              note: "Across everyone with a history",
            },
            {
              label: "Watch list",
              value: String(stats.watch),
              note: stats.watch > 0 ? "A no-show or late cancellation in 90 days" : "No recent problems",
              tone: stats.watch > 0 ? "warning" : "success",
            },
          ]}
        />
      </div>

      <div className="wk-filters">
        {FILTERS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={filter === item.key ? "on" : ""}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
            <small>{counts[item.key]}</small>
          </button>
        ))}
        <span className="wk-count">{visible.length} shown</span>
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title={rows.length === 0 ? "No workers yet" : "Nobody matches"}
          message={
            rows.length === 0
              ? "People who apply to your shifts appear here, with their reliability and history at your venue."
              : "Try a different search or filter."
          }
        />
      ) : (
        <div className="wk-layout">
          <RosterTable
            rows={visible}
            sort={sort}
            selectedId={selected?.worker.worker_id ?? null}
            onSort={setSort}
            onSelect={(row) => setSelectedId(row.worker.worker_id)}
          />

          {selected && <RosterRail row={selected} now={now} />}
        </div>
      )}
    </div>
  );
}
