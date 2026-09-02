import { useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ErrorCard } from "../components/ErrorCard";
import { PageHeader } from "../components/PageHeader";
import { SkeletonCard } from "../components/SkeletonCard";
import { useToast } from "../components/Toast";
import { formatMoney } from "../lib/format";
import { useVenue } from "../lib/useVenue";
import { StatRow } from "./dashboard/StatRow";
import { RosterTable } from "./workers/RosterTable";
import { RosterRail } from "./workers/RosterRail";
import { useDirectory } from "./workers/useDirectory";
import {
  FILTERS,
  directoryStats,
  filterDirectory,
  sortDirectory,
  type DirectoryFilter,
  type DirectorySort,
} from "./workers/directory";
import "./WorkersPage.css";

export function WorkersPage() {
  const { toast } = useToast();
  const venue = useVenue();
  const actions = useDirectory((type, message) => toast({ type, message }));
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<DirectoryFilter>("all");
  const [sort, setSort] = useState<DirectorySort>("name");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (actions.people.error) return <ErrorCard message={(actions.people.error as Error).message} />;
  if (actions.people.isPending || !actions.people.data) {
    return (
      <div className="pg">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={6} />
      </div>
    );
  }

  const currency = venue.data?.currency ?? "GBP";
  const entries = actions.people.data;
  const stats = directoryStats(entries);
  const visible = sortDirectory(filterDirectory(entries, query, filter), sort);
  const selected = visible.find((entry) => entry.worker_id === selectedId) ?? visible[0];

  return (
    <div className="pg">
      <PageHeader
        title="People"
        lead={
          entries.length === 0
            ? "Nobody has worked with you yet."
            : "Everyone you work with, in one place."
        }
        emphasis={stats.counts.team > 0 ? `${stats.counts.team} on your team.` : undefined}
        search={{ value: query, placeholder: "Name or role", onChange: setQuery }}
      />

      <div className="wk-summary">
        <StatRow
          stats={[
            { label: "Your team", value: String(stats.counts.team), note: "Permanent, part time and bank" },
            { label: "Your pool", value: String(stats.counts.pool), note: "Flexible workers you have kept" },
            {
              label: "Worked once",
              value: String(stats.counts.once),
              note: "Hired from the market, not yet in your pool",
            },
            {
              label: "Wages to date",
              value: formatMoney(stats.wages, currency),
              note: `${formatMoney(stats.fees, currency)} in platform fees`,
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
            <small>{stats.counts[item.key]}</small>
          </button>
        ))}
        <span className="wk-count">{visible.length} shown</span>
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title={entries.length === 0 ? "Nobody here yet" : "Nobody matches"}
          message={
            entries.length === 0
              ? "People who work a shift with you appear here. Keep the good ones by adding them to your team."
              : "Try a different search or filter."
          }
        />
      ) : (
        <div className="wk-layout">
          <RosterTable
            rows={visible}
            sort={sort}
            currency={currency}
            selectedId={selected?.worker_id ?? null}
            onSort={setSort}
            onSelect={(entry) => setSelectedId(entry.worker_id)}
          />

          {selected && <RosterRail entry={selected} actions={actions} currency={currency} />}
        </div>
      )}
    </div>
  );
}
