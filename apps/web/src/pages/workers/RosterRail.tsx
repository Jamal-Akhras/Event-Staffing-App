import { WorkerRail } from "../../components/WorkerRail";
import { shortDay } from "../dashboard/dashboardUtils";
import type { RosterRow } from "./rosterUtils";
import { useWorkerHistory } from "./useWorkerHistory";

export function RosterRail({ row, now }: { row: RosterRow; now: Date }) {
  const history = useWorkerHistory(row.worker.worker_id, now);
  return (
    <WorkerRail
      worker={row.worker}
      kicker="Worker"
      stats={[
        { label: "With you", value: `${row.shiftsWithYou} shifts` },
        { label: "Last worked", value: row.lastWorked ? shortDay(row.lastWorked) : "Never" },
      ]}
      historyTitle="Recent shifts with you"
      history={history}
      note={{
        kicker: "Standing",
        title: "How these are worked out",
        body: "Regular means three or more completed shifts with you. Watch flags anyone with a no-show or a worker cancellation in the last 90 days.",
      }}
    />
  );
}
