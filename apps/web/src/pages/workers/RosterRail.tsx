import { useQuery } from "@tanstack/react-query";

import { SkeletonCard } from "../../components/SkeletonCard";
import { WorkerRail } from "../../components/WorkerRail";
import { fetchJson } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import type { WorkerProfile } from "../../types/operations";
import { RELATIONSHIP_LABELS } from "../../types/workforce";
import { shortDay } from "../dashboard/dashboardUtils";
import { RelationshipControls } from "./RelationshipControls";
import type { DirectoryEntry } from "./directory";
import type { useDirectory } from "./useDirectory";
import { useWorkerHistory } from "./useWorkerHistory";

type Props = {
  entry: DirectoryEntry;
  actions: ReturnType<typeof useDirectory>;
  currency: string;
};

function standing(entry: DirectoryEntry): string {
  if (entry.status === "invited") return "Invited, not yet accepted";
  if (entry.status === "ended") return "No longer working with you";
  return RELATIONSHIP_LABELS[entry.relationship_type];
}

export function RosterRail({ entry, actions, currency }: Props) {
  const now = new Date();
  const history = useWorkerHistory(entry.worker_id, now);
  const profile = useQuery({
    queryKey: ["worker-profile", entry.worker_id],
    queryFn: () => fetchJson<WorkerProfile>(`/workers/${entry.worker_id}`),
  });

  if (!profile.data) return <SkeletonCard lines={6} />;

  return (
    <WorkerRail
      worker={profile.data}
      kicker={standing(entry)}
      actions={<RelationshipControls entry={entry} actions={actions} />}
      stats={[
        { label: "With you", value: `${entry.shifts_with_you} shifts` },
        { label: "Hours", value: entry.shifts_with_you ? entry.hours_with_you : "—" },
        { label: "Wages to date", value: formatMoney(entry.wages_to_date, currency) },
        { label: "Last worked", value: entry.last_worked ? shortDay(entry.last_worked) : "Never" },
      ]}
      historyTitle="Recent shifts with you"
      history={history}
      note={{
        kicker: "Relationship",
        title: standing(entry),
        body:
          entry.relationship_type === "one_off"
            ? "They were hired from the open market. Add them to your team and future shifts reach them first."
            : entry.relationship_type === "pool"
              ? "In your pool. They see your shifts before the open market does."
              : "Employed by you. Rostering them never generates a platform fee.",
      }}
    />
  );
}
